# -*- coding: utf-8 -*-
# @Time    : 2022/12/28 11:49 
# @Author  : xzr
# @File    : perf_orm_select.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :
import contextlib
import traceback
from collections import OrderedDict
from threading import local as threading_local

from celery.signals import task_prerun, task_postrun
from django.core.exceptions import EmptyResultSet
from django.db import models
from django.db.models import QuerySet, FilteredRelation, Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.manager import BaseManager
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import WhereNode
from framework.middleware import BaseMiddleware
from framework.utils.attribute import CachedClassAttribute
from django.db.models.fields.related_lookups import RelatedExact
from django.conf import settings

req_orm_select_store = threading_local()
req_orm_select_store.current_req_name = None
req_orm_select_store_data = {}


def get_accesss_models_data() -> dict:
    current_req_name = getattr(req_orm_select_store, 'current_req_name', None)
    return req_orm_select_store_data.setdefault(current_req_name, {}) if current_req_name else None


def add_access_models_field(model_cls, field_name):
    accesss_models_data = get_accesss_models_data()
    if accesss_models_data is not None:
        accesss_models_data.setdefault(model_cls, set())
        accesss_models_data[model_cls].add(field_name)


def get_req_thread_model_fields(model_cls) -> set:
    accesss_models_data = get_accesss_models_data()
    return set(accesss_models_data.get(model_cls, set()) if accesss_models_data else set())


def check_req_orm_select_init():
    accesss_models_data = get_accesss_models_data()
    return accesss_models_data.get('is_init') if accesss_models_data else False


def reset_req_orm_select_store():
    try:
        accesss_models_data = get_accesss_models_data()
        if accesss_models_data is not None:
            accesss_models_data['is_init'] = True
        del req_orm_select_store.current_req_name
    except Exception as e:
        pass



class JoinFilteredRelation(FilteredRelation):
    """关联 Join on 的条件
    JoinFilteredRelation(
                        datastructure.table_alias,
                        condition=Q(company_id=company_id)
                    )
    """
    def __init__(self, relation_alias, condition):
        super().__init__(relation_alias, condition=condition)
        self.alias = self.relation_name

    def __eq__(self, other):
        if other is None:
            return True
        return (
                self.relation_name == other.relation_name and
                self.alias == other.alias and
                self.condition == other.condition
        )
    def as_sql(self, compiler, connection):
        qn = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
        field_name, value = self.condition.children[0]
        sql, params = f'{qn(self.relation_name)}.{qn2(field_name)} = %s', [value]
        return sql, params

    @classmethod
    def has_join_field(cls, field_name, join_model, related_model):
        """join的两个 model 是否用关联字段"""
        return cls.has_relation_field(field_name, join_model) and cls.has_relation_field(field_name, related_model)

    @classmethod
    def has_relation_field(cls, field_name, model):
        return isinstance(getattr(model, 'concrete_fields_map', {}).get(field_name), models.ForeignKey)

    @classmethod
    def has_relation_filter(cls, base_table_alias, field_name, where: WhereNode):
        field_attrname = f'{field_name}_id'
        for child in where.children:
            if isinstance(child, RelatedExact):
                if child.lhs.alias == base_table_alias and child.lhs.field.attname == field_attrname:
                    return True
        return False


class PerfOrmSelectQuerySet(QuerySet):
    _queryset_handlers = set()

    def set_relation_filter(self, field_name, value):
        queryset = self
        model_cls: PerfOrmSelectModel = queryset.model
        fields_map = getattr(model_cls, 'concrete_fields_map', {})
        filter_map = {}
        try:
            if settings.DEBUG:
                print('set_relation_filter', queryset.db, queryset.query.base_table, len(queryset.query.where.children))
            if fields_map and queryset.query.base_table:
                field_name_attrname = f'{field_name}_id'
                model_field = fields_map.get(field_name)
                if isinstance(model_field, models.ForeignKey):
                    filter_map[field_name_attrname] = value
                    if not JoinFilteredRelation.has_relation_filter(queryset.query.base_table, field_name, queryset.query.where):
                        queryset.query.add_q(Q(**filter_map))
                    if queryset.query.select_related or queryset.query.values_select:
                        # 这里要执行下，queryset.query.alias_map 才有值
                        if not queryset.query.is_empty():
                            queryset.query.get_compiler(queryset.db).as_sql()
                        # 增加 join on a.field_name_id=b.field_name_id
                        for table_name in queryset.query.alias_map.keys():
                            datastructure: Join = queryset.query.alias_map[table_name]
                            if isinstance(datastructure, Join):
                                join_model = datastructure.join_field.model
                                related_model = datastructure.join_field.related_model
                                if JoinFilteredRelation.has_join_field(field_name, join_model, related_model):
                                    if (field_name_attrname, field_name_attrname) not in datastructure.join_cols:
                                        datastructure.join_cols += ((field_name_attrname, field_name_attrname),)
                                    if not datastructure.filtered_relation:
                                        datastructure.filtered_relation = JoinFilteredRelation(
                                                datastructure.table_alias,
                                                condition=Q(**filter_map)
                                        )
        except KeyError as e:
            pass
        except EmptyResultSet as e:
            pass
        return self

    @classmethod
    def register_queryset_handler(cls, queryset_handler):
        """不能使用返回 copy 对象的方法，例如 filter only 之类的"""
        cls._queryset_handlers.add(queryset_handler)

    def get_req_thread_fields(self) -> set:
        return get_req_thread_model_fields(self.model)

    def _set_related_select_fields(self, target_select_fields, model, parent_field_name, field_name, parent_dict, cur_depth=0):
        select_fields = target_select_fields
        if cur_depth < self.query.max_depth:
            related_field = model.concrete_fields_map.get(field_name) or model.related_objects_map.get(field_name)
            related_model = related_field.related_model
            model_only_fields = get_req_thread_model_fields(related_model)
            if parent_field_name:
                prefix_lookup_sep = f'{parent_field_name}{LOOKUP_SEP}'
            else:
                prefix_lookup_sep = f'{field_name}{LOOKUP_SEP}'
                
            for related_model_field_name in model_only_fields:
                select_fields.add(f'{prefix_lookup_sep}{related_model_field_name}')

            if not model_only_fields:
                if parent_field_name:
                    select_fields.add(f'{prefix_lookup_sep}{model._meta.pk.attname}')
                else:
                    select_fields.add(f'{prefix_lookup_sep}{related_model._meta.pk.attname}')

            if parent_dict:
                for child_field_name, child_dict in parent_dict.items():
                    parent_field_name = f'{prefix_lookup_sep}{child_field_name}'
                    self._set_related_select_fields(select_fields, related_model, parent_field_name, child_field_name, child_dict, cur_depth + 1)
        return select_fields

    def _deduction_select_field(self):
        # 通过执行一次查询，下次推导字段
        if check_req_orm_select_init() and not self.query.combinator:
            only_model_fields = get_req_thread_model_fields(self.model)
            if only_model_fields:
                only_fields = only_model_fields
                existing, defer = self.query.deferred_loading
                only_select_fields = set()
                if isinstance(self.query.select_related, dict):
                    for select_related_field_name, child_dict in self.query.select_related.items():
                        self._set_related_select_fields(only_select_fields, self.model, '', select_related_field_name, child_dict, 0)
                # 有设置 only  合并 existing 字段
                if not defer and existing:
                    only_fields = existing
                if only_fields:
                    self.query.add_immediate_loading(only_fields|only_select_fields)

    def set_queryset_handler(self):
        for queryset_handler in self.__class__._queryset_handlers:
            if callable(queryset_handler):
                queryset_handler(self)

    def count(self, *args, **kwargs):
        self.set_queryset_handler()
        return super().count(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        self.set_queryset_handler()
        return super().aggregate(*args, **kwargs)

    def _fetch_all(self):
        self._deduction_select_field()
        self.set_queryset_handler()
        return super()._fetch_all()

    def use_indexs(self, table, *indexs, is_force=False):
        clone = self._chain()
        clone.query.get_initial_alias()
        alias_map = clone.query.alias_map
        table_obj = alias_map.get(table)
        if table_obj:
            indexs_str = ','.join(indexs)
            table_alias = table_obj.table_alias
            if indexs_str:
                use_index_mark = 'FORCE' if is_force else 'USE'
                if not f'{use_index_mark} INDEX' in table_obj.table_alias:
                    table_alias = '' if table_obj.table_alias == table_obj.table_name else table_obj.table_name
                    table_alias = f'{table_alias} {use_index_mark} INDEX ({indexs_str})'
            else:
                table_alias = table_obj.table_name
            table_obj.table_alias = table_alias
        return clone

    def force_index(self, table, *indexs):
        return self.use_indexs(table, *indexs, is_force=True)





class PerfOrmSelectManager(BaseManager.from_queryset(PerfOrmSelectQuerySet), models.Manager):
    def get_queryset(self):
        """重写 get_queryset"""
        return super().get_queryset()

class PerfOrmSelectModel(models.Model):
    """优化 orm 查询 字段选择，适合多字段的表
    在一个请求线程内 记录执行模型的 query 后，通过 model 获取的属性名
    instance = Model.objects.first()
    instance.f1
    instance.f2
    下次 Model.objects.first() 自动添加 only  Model.objects.only('f1','f2')
    集成模型后 Meta 添加
    class Meta:
        base_manager_name = 'objects'
    """

    objects = PerfOrmSelectManager()

    _is_load_from_db = False

    class Meta:
        abstract = True
        base_manager_name = 'objects'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.pk and getattr(self, self._meta.pk.attname):
            self._is_load_from_db = True

    def __getattribute__(self, attrname):
        if super().__getattribute__('_is_load_from_db') and attrname in super().__getattribute__('__class__').concrete_fields_map:
            add_access_models_field(self._meta.model, attrname)
        return super().__getattribute__(attrname)

    @CachedClassAttribute
    def concrete_fields_map(cls):
        fields_map = OrderedDict([(field.name, field) for field in cls._meta.concrete_fields if
                                  not field.primary_key])
        # 外键 attrname 也算进去
        for key in list(fields_map.keys()):
            fields_map[fields_map[key].attname] = fields_map[key]
        return fields_map


class PerfOrmSelectMiddleware(BaseMiddleware):
    """优化 orm select 的查询
    """

    def process_request(self, request):
        pass

    def process_view(self, request, view_func, view_args, view_kwargs):

        req_view_func = self.get_check_view_func(request, view_func)
        req_name = f'{req_view_func.__module__}.{req_view_func.__name__}'
        req_orm_select_store.current_req_name = req_name

    def process_response(self, request, response):
        reset_req_orm_select_store()
        return response

    def process_exception(self, request, exception):
        reset_req_orm_select_store()


@task_prerun.connect
def celery_task_prerun_handler(signal, sender, task_id, task, args, kwargs, **extras):
    try:
        req_orm_select_store.current_req_name = task.name
    except Exception as e:
        traceback.print_exc()


@task_postrun.connect
def celery_task_postrun_handler(signal, sender, task_id, task, args, kwargs, retval, state, **extras):
    try:
        reset_req_orm_select_store()
    except Exception as e:
        traceback.print_exc()


@contextlib.contextmanager
def perf_orm_select_context(req_name):
    try:
        req_orm_select_store.current_req_name = req_name
        yield
    finally:
        reset_req_orm_select_store()
