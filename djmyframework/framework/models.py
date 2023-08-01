# -*- coding: utf-8 -*-
import copy
import datetime
import hashlib
import json
import re
import time
from collections import OrderedDict
from urllib.parse import urlparse

import addict
import timezone_field
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.color import no_style
from django.core.validators import RegexValidator
from django.db import close_old_connections, connection
from django.db import models
from django.db.models import JSONField as DjJSONField
from django.db.models import QuerySet
from django.db.models.signals import post_init
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from mptt.querysets import TreeQuerySet
from rest_framework import serializers
from rest_framework.fields import DictField, CharField

from .encryption.aes.aes import AESCrypt
from .perf_orm_select import PerfOrmSelectModel, PerfOrmSelectQuerySet
from .utils import json_dumps, ObjectDict, trace_msg, myenum, MyJsonEncoder
from .utils.cache import CachedClassAttribute
from .utils.log import logger
from .validators import LetterValidator


def truncate_name(name, length=None, hash_len=4):
    """Shortens a string to a repeatable mangled version with the given length.
    """
    if length is None or len(name) <= length:
        return name

    hsh = hashlib.md5(force_bytes(name)).hexdigest()[:hash_len]
    return '%s%s' % (name[:length - hash_len], hsh)


def close_connections():
    try:
        close_old_connections()
    except Exception as e:
        logger.error(e)


class SqlModel(object):
    connection = connection

    @classmethod
    def sql_for_inline_foreign_key_references(cls, model, field, known_models, style):
        """
        Return the SQL snippet defining the foreign key reference for a field.
        """
        qn = cls.connection.ops.quote_name
        rel_to = field.rel.to
        if rel_to in known_models or rel_to == model:
            output = [style.SQL_KEYWORD('REFERENCES') + ' ' +
                      style.SQL_TABLE(qn(rel_to._meta.db_table)) + ' (' +
                      style.SQL_FIELD(qn(rel_to._meta.get_field(
                              field.rel.field_name).column)) + ')' +
                      cls.connection.ops.deferrable_sql()
                      ]
            pending = False
        else:
            # We haven't yet created the table to which this field
            # is related, so save it for later.
            output = []
            pending = True

        return output, pending

    @classmethod
    def sql_create_model(cls, model, style=None, known_models=[]):
        """
        Returns the SQL required to create a single model, as a tuple of:
            (list_of_sql, pending_references_dict)
        """
        style = style or no_style()
        opts = model._meta
        if not opts.managed or opts.proxy or opts.swapped:
            return [], {}
        final_output = []
        table_output = []
        pending_references = {}
        qn = cls.connection.ops.quote_name
        for f in opts.local_fields:
            col_type = f.db_type(connection=cls.connection)
            col_type_suffix = cls.connection.data_types_suffix.get(f.get_internal_type())
            if col_type_suffix:
                col_type += " %s" % col_type_suffix

            tablespace = f.db_tablespace or opts.db_tablespace
            if col_type is None:
                # Skip ManyToManyFields, because they're not represented as
                # database columns in this table.
                continue
            # Make the definition (e.g. 'foo VARCHAR(30)') for this field.
            field_output = [style.SQL_FIELD(qn(f.column)),
                            style.SQL_COLTYPE(col_type)]
            # Oracle treats the empty string ('') as null, so coerce the null
            # option whenever '' is a possible value.
            null = f.null
            if (f.empty_strings_allowed and not f.primary_key and
                    cls.connection.features.interprets_empty_strings_as_nulls):
                null = True
            if not null:
                field_output.append(style.SQL_KEYWORD('NOT NULL'))
            if f.primary_key:
                field_output.append(style.SQL_KEYWORD('PRIMARY KEY'))
            elif f.unique:
                field_output.append(style.SQL_KEYWORD('UNIQUE'))

            if f.has_default():
                default = f.get_default()
                if default in [False, True]:
                    default = str(int(f.get_default()))
                elif isinstance(default, str):
                    default = "'%s'" % default
                else:
                    default = qn(default)
                field_output.append(style.SQL_KEYWORD('DEFAULT') + ' ' + default)

            if tablespace and f.unique:
                # We must specify the index tablespace inline, because we
                # won't be generating a CREATE INDEX statement for this field.
                tablespace_sql = connection.ops.tablespace_sql(
                        tablespace, inline=True)
                if tablespace_sql:
                    field_output.append(tablespace_sql)
            if getattr(f, 'rel', None) and getattr(f, 'db_constraint', None):
                ref_output, pending = cls.sql_for_inline_foreign_key_references(
                        model, f, known_models, style)
                if pending:
                    pending_references.setdefault(f.rel.to, []).append(
                            (model, f))
                else:
                    field_output.extend(ref_output)
            table_output.append(' '.join(field_output))
        for field_constraints in opts.unique_together:
            table_output.append(style.SQL_KEYWORD('UNIQUE') + ' (%s)' %
                                ", ".join(
                                        [style.SQL_FIELD(qn(opts.get_field(f).column))
                                         for f in field_constraints]))

        full_statement = [style.SQL_KEYWORD('CREATE TABLE') + ' ' +
                          style.SQL_TABLE(qn(opts.db_table)) + ' (']
        for i, line in enumerate(table_output):  # Combine and add commas.
            full_statement.append(
                    '    %s%s' % (line, ',' if i < len(table_output) - 1 else ''))
        full_statement.append(')')
        if opts.db_tablespace:
            tablespace_sql = connection.ops.tablespace_sql(
                    opts.db_tablespace)
            if tablespace_sql:
                full_statement.append(tablespace_sql)
        full_statement.append(';')
        final_output.append('\n'.join(full_statement))

        if opts.auto_field:
            # Add any extra SQL needed to support auto-incrementing primary
            # keys.
            auto_column = opts.auto_field.db_column or opts.auto_field.name
            autoinc_sql = connection.ops.autoinc_sql(opts.db_table,
                                                     auto_column)
            if autoinc_sql:
                for stmt in autoinc_sql:
                    final_output.append(stmt)

        return final_output, pending_references

    @classmethod
    def sql_indexes_for_model(self, model, style):
        """
        Returns the CREATE INDEX SQL statements for a single model.
        """
        if not model._meta.managed or model._meta.proxy or model._meta.swapped:
            return []
        output = []
        for f in model._meta.local_fields:
            output.extend(self.sql_indexes_for_field(model, f, style))
        for fs in model._meta.index_together:
            fields = [model._meta.get_field_by_name(f)[0] for f in fs]
            output.extend(self.sql_indexes_for_fields(model, fields, style))
        return output

    @classmethod
    def sql_indexes_for_field(self, model, f, style):
        """
        Return the CREATE INDEX SQL statements for a single model field.
        """
        if f.db_index and not f.unique:
            return self.sql_indexes_for_fields(model, [f], style)
        else:
            return []

    @classmethod
    def sql_indexes_for_fields(self, model, fields, style):
        if len(fields) == 1 and fields[0].db_tablespace:
            tablespace_sql = self.connection.ops.tablespace_sql(fields[0].db_tablespace)
        elif model._meta.db_tablespace:
            tablespace_sql = self.connection.ops.tablespace_sql(model._meta.db_tablespace)
        else:
            tablespace_sql = ""
        if tablespace_sql:
            tablespace_sql = " " + tablespace_sql

        field_names = []
        qn = self.connection.ops.quote_name
        for f in fields:
            field_names.append(style.SQL_FIELD(qn(f.column)))

        index_name = "%s_%s" % (model._meta.db_table, self._digest([f.name for f in fields]))

        return [
                style.SQL_KEYWORD("CREATE INDEX") + " " +
                style.SQL_TABLE(qn(truncate_name(index_name, self.connection.ops.max_name_length()))) + " " +
                style.SQL_KEYWORD("ON") + " " +
                style.SQL_TABLE(qn(model._meta.db_table)) + " " +
                "(%s)" % style.SQL_FIELD(", ".join(field_names)) +
                "%s;" % tablespace_sql,
        ]

    @classmethod
    def _digest(self, *args):
        """
        Generates a 32-bit digest of a set of arguments that can be used to
        shorten identifying names.
        """
        h = hashlib.md5()
        for arg in args:
            h.update(force_bytes(arg))
        return h.hexdigest()[:8]


class SqlModelMixin(object):

    @classmethod
    def get_create_model_indexs(cls):
        return SqlModel.sql_indexes_for_model(cls, no_style())

    @classmethod
    def get_create_model_sql(cls, replace_table_name='') -> str:
        """获取创建模型的SQL语句
        @replace_table_name 需要替换的表名
        """

        sql, _ = SqlModel.sql_create_model(cls, no_style())
        sql = sql[0].replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS').rstrip(';')
        sql = '%s ENGINE=InnoDB ;' % sql
        if replace_table_name:
            sql = sql.replace(cls._meta.db_table, replace_table_name)
        return sql

    @classmethod
    def get_db_name(cls):
        return settings.DATABASES.get(cls.objects.db, {}).get('NAME', '')

    @classmethod
    def get_app_name(cls):
        return cls._meta.app_label

    @classmethod
    def get_table_name(cls):
        """返回模型的表名
        """
        return cls._meta.db_table


class BaseModelMixin(SqlModelMixin):
    """
    基本模型混合方法
    """

    def is_related_field(self, field):
        return isinstance(field, (models.ForeignKey, models.ManyToManyField, models.OneToOneRel))

    @classmethod
    def create_or_update_for_params(cls, params_dict, ignore_list=()):
        err_msg = ''
        model = None

        try:
            _id = int(params_dict.get('id', '') or 0)

            if _id:
                model = cls.objects.get(id=_id)
            else:
                model = cls()
            keys = params_dict.keys()
            for f in cls.get_fields():
                field_name = f.get_attname()
                if field_name in ignore_list or field_name == 'id' or field_name not in keys:
                    continue
                value = params_dict.get(field_name, None)

                value = f.to_python(value)
                if not (not f.null and value is None):
                    setattr(model, field_name, value)
        except Exception as e:
            logger.error(e)
            err_msg = trace_msg()
        return err_msg, model

    def is_attr_instance(self, attr, cla):
        return isinstance(getattr(self, attr), cla)

    def set_attrs_for_dict(self, dict_data, use_default=False):
        for f in self.get_fields(has_private=True):
            if isinstance(f, (models.ManyToManyField,)) or f.attname == 'id':
                continue
            field_name = f.name
            data = dict_data.get(f.name, models.fields.Empty)
            if data is not models.fields.Empty:
                if isinstance(f, (models.ForeignKey, models.OneToOneRel)):
                    if not isinstance(data, (models.Model, int)):
                        continue
                if f.default is not models.fields.NOT_PROVIDED and use_default:
                    data = f.default
                if not f.null and data is None:
                    continue
                self.set_attr(field_name, data, null=True)

    def set_attr(self, name, value, value_handler=None, null=False):
        """设置模型的属性
        """

        if value_handler:
            value = value_handler(value)
        if not null:
            assert value != None and value != '', '%s 不能为空!' % self.get_verbose_name(name)
        setattr(self, name, value)

    def to_dict(self, ignore_list=(), has_m2mfields=False, is_msgpack=False):
        d = {}
        for field in self._meta.fields:
            attr = field.name

            attr_value = self.__dict__.get(attr)  # getattr(self, attr)

            # 特殊处理datetime的数据
            if isinstance(attr_value, datetime.datetime) and is_msgpack:
                d[attr] = attr_value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(attr_value, datetime.date) and is_msgpack:
                d[attr] = attr_value.strftime('%Y-%m-%d')
            # 递归生成BaseModel类的dict
            elif isinstance(attr_value, BaseModel):
                d[attr] = attr_value.get_dict(has_m2mfields=has_m2mfields, is_msgpack=is_msgpack)
            elif isinstance(attr_value, (int, str, float)):
                d[attr] = attr_value
            elif not is_msgpack:
                d[attr] = field.get_prep_value(attr_value)

        if has_m2mfields:
            m2mfields = self.__class__._meta.many_to_many
            if m2mfields:
                for m in m2mfields:
                    attr_name = m.attname
                    if hasattr(self, attr_name):
                        attlist = getattr(self, attr_name).all()
                        l = []
                        for attr in attlist:
                            if isinstance(attr, BaseModel):
                                l.append(attr.to_dict(is_msgpack=is_msgpack))
                            else:
                                dic = attr.__dict__
                                if '_state' in dic:
                                    dic.pop('_state')
                                l.append(dic)
                        d[attr_name] = l
        # 由于ManyToMany类不能存在于_meat.fields，因而子类需要在getMtMFiled中返回这些字段
        if 'basemodel_ptr' in d:
            d.pop('basemodel_ptr')

        if ignore_list:
            for m in ignore_list:
                if d.get(m) is not None:
                    d.pop(m)
        # 移除不需要的字段
        return d

    get_dict = to_dict

    @property
    def addict(self):
        return addict.Addict(
                {field.name: self.__dict__.get(field.name) for field in self._meta.fields if field.name in self.__dict__}
        )

    def to_json(self, ignore_list=()):
        return json_dumps(self.to_dict(ignore_list))

    def get_verbose_name(self, field_name):
        """返回模型属性描述
        """
        for x in self.__class__.get_fields():
            if field_name == x.name:
                return x.verbose_name

    @classmethod
    def get_list_view_name(cls, model_class=None):
        model_class = model_class or cls
        return '%s.%s.list' % (model_class._meta.app_label, cls.get_lower_name(model_class))

    @classmethod
    def get_list_url(cls):
        return reverse(cls.get_list_view_name())

    @CachedClassAttribute
    def lower_name(cls):
        return cls.get_lower_name()

    @classmethod
    def get_lower_name(cls, model_class=None):
        new_lower_name_list = []
        name_str = model_class.__name__ if model_class else cls.__name__
        for i, c in enumerate(name_str):
            if i > 0 and c.isupper():
                if name_str[i - 1].islower() or name_str[i + 1].islower():
                    new_lower_name_list.append('_')
            new_lower_name_list.append(c.lower())
        return ''.join(new_lower_name_list)

    @classmethod
    def get_db_name(cls):
        return settings.DATABASES.get(cls.objects.db, {}).get('NAME', '')

    @classmethod
    def get_app_name(cls):
        return cls._meta.app_label

    @classmethod
    def get_table_name(cls):
        """返回模型的表名
        """
        return cls._meta.db_table

    @classmethod
    def get_fields_name_list(cls, ignore_keys=('id',)):
        return [f.get_attname() for f in cls.get_fields() if f.attname not in ignore_keys]

    @CachedClassAttribute
    def fields(cls):
        opts = cls._meta
        from django.db.models.fields import Field as ModelField
        from itertools import chain
        sortable_private_fields = [f for f in opts.private_fields if isinstance(f, ModelField)]
        return [f for f in sorted(chain(opts.concrete_fields, sortable_private_fields, opts.many_to_many))]

    @classmethod
    def get_fields(cls, has_private=False):
        """返回模型的相关字段定义
        """
        return [f for f in cls.fields if
                has_private or not f.name.startswith('_')]

    @classmethod
    def get_many_to_many_fileds(cls):
        return cls._meta.many_to_many

    @CachedClassAttribute
    def fields_map(cls):
        return cls.get_fields_map()

    @classmethod
    def get_fields_map(cls):
        field_dict = OrderedDict([(f.name, f) for f in cls.get_fields()])
        return field_dict

    @classmethod
    def prefetch_related_all(cls) -> QuerySet:
        return cls.objects.prefetch_related(*[f.attname for f in cls._meta.many_to_many])

    @classmethod
    def get_related_objects(cls) -> QuerySet:
        """获取模型所有关联字段"""
        return cls.prefetch_related_all().select_related(
                *[f.attname for f in cls.get_fields() if isinstance(f, (models.ForeignKey, models.OneToOneRel))])

    @CachedClassAttribute
    def concrete_fields_map(cls):
        fields_map = OrderedDict([(field.name, field) for field in cls._meta.concrete_fields if
                                  not field.primary_key])
        # 外键 attrname 也算进去
        for key in list(fields_map.keys()):
            fields_map[fields_map[key].attname] = fields_map[key]
        return fields_map

    @CachedClassAttribute
    def related_objects_map(cls):
        fields_map = OrderedDict([(field.name, field) for field in cls._meta.related_objects])

        return fields_map

    def copy(self):
        copy_obj = copy.copy(self)
        copy_obj.id = None
        return copy_obj


class OptimisticLockException(Exception): pass


class BaseModel(PerfOrmSelectModel, BaseModelMixin):
    id = models.BigAutoField(primary_key=True)
    _version = models.IntegerField(_("版本"), default=0, null=False)

    # auto_now_add = True    #创建时添加的时间  修改数据时，不会发生改变
    create_datetime = models.DateTimeField(_("创建时间"), auto_now_add=True, blank=True, null=False, db_index=True)
    update_datetime = models.DateTimeField(_("更新时间"), auto_now=True, blank=True, null=False)

    _is_init = False

    class Meta:
        abstract = True
        ordering = ['id']

    def __init__(self, *args, **kwargs):
        self._update_fields = set()
        super().__init__(*args, **kwargs)
        self._is_init = True

    def _get_update_fields(self):
        """通过判断初始值是否有变化，而更新相应字段"""
        pre_init_data = getattr(self, 'pre_init_data', None)
        if pre_init_data:
            _update_fields = set()
            is_second_save = self._version - pre_init_data.get('_version', self._version) > 1
            self._is_init = False
            for field_name in self._update_fields:
                field = self.concrete_fields_map.get(field_name)
                if field:
                    attname = field.attname
                    init_value = pre_init_data.get(attname, models.fields.Empty)
                    new_value = getattr(self, attname)
                    if new_value != init_value or isinstance(init_value, (dict, list, tuple, set)) or is_second_save:
                        _update_fields.add(attname)
            if is_second_save:
                pre_init_data['_version'] = self._version
            self._is_init = True
            return _update_fields
        return self._update_fields

    def _optimistic_save_again(self, new_data: dict, look_num: int, *args, **kwargs):
        """
        乐观锁保存失败，尝试从数据库中刷新值再对比差异
        @return:
        """
        pre_init_data = getattr(self, 'pre_init_data', None)
        if pre_init_data:
            self.refresh_from_db()
            new_data.pop('_version', None)
            for attr_name, update_value in new_data.items():
                value = getattr(self, attr_name)
                init_value = pre_init_data.get(attr_name, models.fields.Empty)
                if init_value is not models.fields.Empty:
                    new_value = update_value
                    if isinstance(value, (int, float)):
                        diff_value = update_value - init_value
                        new_value = value + diff_value
                    setattr(self, attr_name, new_value)
            return self.optimistic_save(look_num=look_num, *args, **kwargs)

    def optimistic_save(self, *args, raise_exception=True, look_num=3, **kwargs):
        """
        乐观锁 保存
        @param args:
        @param raise_exception:
        @param look_num: 更新失败重试次数
        @param kwargs:
        @return:
        """
        if self.id:
            new_data = {field_name: getattr(self, field_name) for field_name in self._get_update_fields()}
            # new_data = {f.name: getattr(self, f.name) for f in self.get_fields(has_private=True) if  not self.is_related_field(f)}

            new_data['_version'] = self._version + 1
            new_data['update_time'] = datetime.datetime.now()
            has_save = self.__class__.objects.using(kwargs.get('using')).filter(id=self.id,
                                                                                _version=self._version,
                                                                                ).update(**new_data)
            if has_save:
                self._version = new_data['_version']
            else:
                _look_num = look_num - 1
                if look_num >= 0:
                    time.sleep(0.01)
                    has_save = self._optimistic_save_again(new_data, look_num=_look_num)
                if not has_save:
                    if raise_exception:
                        raise OptimisticLockException(f'{self} {self.id} {self._version} Optimistic Save Error look_num: {look_num}')
            return has_save
        else:
            return self.save(*args, **kwargs)

    def __getattribute__(self, attrname):
        if super().__getattribute__('_is_init') and attrname in super().__getattribute__('concrete_fields_map'):
            super().__getattribute__('_update_fields').add(attrname)
        return super().__getattribute__(attrname)

    def __setattr__(self, attrname, value):
        if self._is_init and attrname in self.concrete_fields_map:
            self._update_fields.add(attrname)
        return super().__setattr__(attrname, value)

    def save(self, *args, **kwargs):
        """只更新有改的字段"""
        self.update_datetime = datetime.datetime.now()
        self._version += 1
        update_fields = kwargs.pop('update_fields', None)
        if self.id and not kwargs.get('force_insert'):
            update_fields = update_fields or self._get_update_fields()
        return super().save(*args, update_fields=update_fields, **kwargs)


class BaseNameModel(BaseModel):
    name = models.CharField(_('名称'), max_length=100, null=False, blank=False, validators=[LetterValidator],
                            unique=True)

    alias = models.CharField(_('别名'), max_length=100, default='', null=False, blank=True)

    class Meta:
        abstract = True


class JSONField(DjJSONField):
    def __init__(self, verbose_name=None, name=None, encoder=None, decoder=None, **kwargs):
        super().__init__(verbose_name, name, **kwargs)
        self.encoder = self.encoder or MyJsonEncoder

    def _check_default(self):
        return []

    def get_default(self):
        default = super().get_default()
        return copy.deepcopy(default)


class _JSONField(models.TextField):
    """旧的不用,用 django 3 的"""
    description = "Json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_default(self):
        default = super().get_default()
        return copy.deepcopy(default)

    def from_db_value(self, value, expression=None, connection=None):
        return self.to_python(value)

    def to_python(self, value):

        if not isinstance(value, str):
            return value
        try:

            _r = json.loads(value)
        except Exception as e:
            logger.error('to_python Failed.', exc_info=e)
            _r = {}
        return _r

    def get_prep_value(self, value):
        try:
            if isinstance(value, str):
                json.loads(value)
                _v = value
            else:
                _v = json_dumps(value)
        except Exception as e:
            logger.error('get_prep_value Failed. %s' % value, exc_info=e)
            _v = '{}'
        return _v


class URLTrokenField(models.URLField):
    """生成的链接地址带上token"""
    _iv = b'\x9b+\x16U\xabZ\xfb\x91\x0bLd\xa7\xd9\x05\xde]'

    def from_db_value(self, value, expression=None, connection=None):
        return self.to_python(value)

    def to_python(self, value):
        if value:
            return self.set_token(value)
        return value

    def set_token(self, url):
        # todo 阿里云 oss 的？
        url_p = urlparse(url)
        token = AESCrypt(settings.SECRET_KEY[:32], self._iv).encrypt(str(int(time.time()))).hex()
        # url = url_p._replace(query='_tk=%s&%s' % (token, url_p.query)).geturl()
        url = url_p._replace(query='_tk=%s' % token).geturl()
        return url

    def check_token(self, token):
        """检验token
        5分钟内有效"""

        try:
            t = AESCrypt(settings.SECRET_KEY[:32], self._iv).decrypt(bytes.fromhex(token))
            if int(time.time()) - int(t) < 60 * 5:
                return True
        except Exception as error:
            return False

    def get_prep_value(self, value):
        return value


class ObjectDictField(models.TextField):
    """ObjectDictField is a textfield that contains JSON-serialized dictionaries."""
    description = "ObjectDict"

    def __init__(self, *args, **kwargs):
        if not kwargs.get('default', None):
            kwargs['default'] = ObjectDict()
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression=None, connection=None):
        return self.to_python(value)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        try:
            if isinstance(value, str):
                value = json.loads(value)
        except Exception as e:
            logger.error('to_python. %s' % value, exc_info=e)
            value = {}
        return ObjectDict(value)

    def get_prep_value(self, value):
        try:
            if isinstance(value, dict):
                return json_dumps(value)
            return value
        except Exception as e:
            logger.error('Failed. %s' % value, exc_info=e)
            return '{}'


serializers.ModelSerializer.serializer_field_mapping[ObjectDictField] = DictField
serializers.ModelSerializer.serializer_field_mapping[timezone_field.TimeZoneField] = CharField


def validate_re(value, pattern='', err_msg=''):
    if not re.match(pattern, value):
        raise ValidationError(err_msg)


def get_re_validate(pattern='', err_msg=''):
    """
    根据正则，返回参数验证函数

    :param pattern:
    :param err_msg:
    :return: partial
    """
    return RegexValidator(validate_re, err_msg)


class ModelStatus(myenum.Enum):
    delete = (0, _('删除'))
    enable = (1, _('正常'))
    disable = (2, _('禁用'))
    expire = (3, _('过期'))
    unknown = (4, _('未知'))


class BaseStatusModel(BaseModel):
    STATUS = ModelStatus
    status = models.SmallIntegerField('状态', null=False, choices=ModelStatus.choices, default=ModelStatus.enable)

    def remove(self):
        self.status = ModelStatus.delete
        self.save()

    class Meta:
        abstract = True


@receiver(post_init)
def model_init(sender, instance, **kwargs):
    """所有模型初始化的时候,复制一份初始化数据
    """
    # from django.forms.models import model_to_dict
    if getattr(instance, "pk", None):
        pre_init_data = ObjectDict(instance.__dict__)
    else:
        pre_init_data = ObjectDict()
    instance.pre_init_data = pre_init_data


class PerfOrmSelectTreeQuerySet(PerfOrmSelectQuerySet, TreeQuerySet): pass


class PerfOrmSelectTreeManager(models.Manager.from_queryset(PerfOrmSelectTreeQuerySet), TreeManager): pass


class TreeModel(PerfOrmSelectModel, MPTTModel):
    """MPTT模型实例方法:
    https://www.cnblogs.com/wuzdandz/p/10595416.html
    https://django-mptt.readthedocs.io/en/latest/
    get_ancestors(ascending=False, include_self=False)  # 返回一个包含所有当前实例祖宗的queryset
    get_children()  # 返回包换当前实例的直接孩子的queryset(即下一级所有的子节点)，按树序排列
    get_descendants(include_self=False)  # 返回当前实例的所有子节点，按树序排列
    get_descendant_count()  # 返回当前实例所有子节点的数量
    get_family()  # 返回从当前实例开始的所有家庭成员节点，用树型结构
    get_next_sibling()  # 返回当前实例的下一个树型同级节点的实例
    get_previous_sibling()  # 返回当前实例的上一个树型同级节点的实例
    get_root()  ＃ 获取当前实例的根节点实例
    get_siblings(include_self=False)  # 获取所有同级兄弟节点的实例的queryset
    insert_at(target, position='first-child', save=False)  # 插入作为目标节点的第一个子节点(如果save=True)
    is_child_node()  # 是否是子节点
    is_leaf_node()  # 是否是叶节点
    is_root_node()  # 是否是根节点
    move_to(target, position='first-child')  # 移动到某个节点的第一个子节点位置，target为空将会被移到根节点，此时不需要position位置参数
    position位置参数:
    'first-child', 'last-child','left', 'right'
    """

    objects = PerfOrmSelectTreeManager()

    parent = TreeForeignKey('self', verbose_name='上级ID', null=True, on_delete=models.CASCADE, blank=True,
                            related_name='children', db_constraint=False)

    @property
    def has_children(self):
        return not self.is_leaf_node() and len(self.children.all()) > 0

    class Meta:
        abstract = True
        base_manager_name = 'objects'
        default_manager_name = 'objects'


class AttributeModel(PerfOrmSelectModel, BaseModelMixin):
    """
    attribute 配置属性 高级版 多配置自用
    """

    class Meta:
        abstract = True

    # ATTRIBUTE_CONF = []
    # attribute = models.PositiveIntegerField('二进制配置', default=0, blank=True, null=True)  # 参考 Bilibili attribute 8bit

    def attribute_item(self, attribute, _attribute_list=None) -> dict:
        result = {}
        for attr_name in _attribute_list:
            result[attr_name] = self.get_attribute(attr_name, attribute, _attribute_list)
        return result

    def get_attribute(self, attr_name, attribute=0, _attribute_list=None) -> bool:
        # _attribute_list = _attribute_list if _attribute_list else self.ATTRIBUTE_CONF
        _index = _attribute_list.index(attr_name)
        return True if attribute & (1 << _index) else False

    def set_attribute(self, items: dict, attribute=0, _attribute_list=None) -> int:
        """ items{conf_name:bool} -> attribute # batch modify"""
        # _attribute_list = _attribute_list if _attribute_list else self.ATTRIBUTE_CONF
        for attribute_name, _bool in items.items():
            _index = _attribute_list.index(attribute_name)
            attribute = attribute | (1 << _index) if _bool else attribute & ~(1 << _index)
        return attribute

    def modify_attribute(self, attribute_name: str, _val: bool, attribute=0, _attribute_list=None) -> int:
        """ attribute_name:conf_name _val:bool -> attribute """
        # _attribute_list = _attribute_list if _attribute_list else self.ATTRIBUTE_CONF
        _index = _attribute_list.index(attribute_name)
        return attribute | (1 << _index) if _val else attribute & ~(1 << _index)


class SimpleAttributeModel(PerfOrmSelectModel, BaseModelMixin):
    """
    简单易用的配置属性模型
    灵感来自啊B 原理是 bit 按位标识配置开关 存储在十进制数字里面(参考 Redis Bitmap 可存放大量配置项,或者做签到,登陆统计,用户状态记录)
    """

    class Meta:
        abstract = True

    # ATTRIBUTE_CONF = []
    # attribute = models.PositiveIntegerField('二进制配置', default=0, blank=True, null=True)  # max len 31

    def attribute_item(self) -> dict:
        return {attr_name: self.get_attribute(attr_name) for attr_name in self.ATTRIBUTE_CONF}

    def attribute_list(self) -> list:
        return list(filter(lambda _: _, self.attribute_item()))

    def get_attribute(self, attr_name) -> bool:
        return True if self.attribute & (1 << self.ATTRIBUTE_CONF.index(attr_name)) else False

    @classmethod
    def set_attribute(cls, items: dict) -> int:
        attribute = 0
        for attribute_name, _bool in items.items():
            _index = cls.ATTRIBUTE_CONF.index(attribute_name)
            attribute = attribute | (1 << _index) if _bool else attribute & ~(1 << _index)
        return attribute

    def modify_attribute(self, attribute_name: str, _val: bool) -> int:
        """ attribute_name:conf_name _val:bool -> attribute """
        _index = self.ATTRIBUTE_CONF.index(attribute_name)
        return self.attribute | (1 << _index) if _val else self.attribute & ~(1 << _index)


class ShardingModelMixin(object):
    """分表的模型"""

    # 预先创建的分表数量
    pre_sharding_num = 12

    __sharding_model_cls_cache = {}

    last_create_time = None

    @classmethod
    def get_sharding_key(cls, sharding_num):
        return str(sharding_num)

    @classmethod
    def create_sharding_table(cls):
        """
        预先创建分表
        @return:
        """
        for i in range(cls.pre_sharding_num):
            sharding_key = cls.get_sharding_key(i)
            dst_table = cls.get_shanrding_table_name(sharding_key)
            sql = f'CREATE TABLE IF NOT EXISTS {dst_table} LIKE {cls._meta.db_table}'
            with connection.cursor() as cursor:
                print(sql)
                # cursor.execute(sql)

    @classmethod
    def get_shanrding_table_name(cls, shanrding_key):
        return f'{cls._meta.db_table}_{shanrding_key}'

    @classmethod
    def get_sharding(cls, shanrding_key=''):  # type: () -> cls
        cls._meta.abstract = True

        if not cls.last_create_time:
            cls.create_sharding_table()
            cls.last_create_time = datetime.datetime.now()
        model_cls = cls.__sharding_model_cls_cache.get(shanrding_key, None)
        if not model_cls:
            class Meta:
                app_label = cls._meta.app_label
                db_table = cls.get_shanrding_table_name(shanrding_key)

            attrs = {
                    '__module__': cls.__module__,
                    'Meta'      : Meta
            }
            model_cls = type(str(f'{cls.__name__}_{shanrding_key}'), (cls,), attrs)
            cls.__sharding_model_cls_cache[shanrding_key] = model_cls
        return model_cls


class MonthShardingModel(ShardingModelMixin):
    """按月分表"""

    table_date_fmt = '%Y%m01'

    @classmethod
    def get_sharding_key(cls, sharding_num):
        now = datetime.datetime.now()
        date = now + relativedelta(months=sharding_num)
        month_text = date.strftime(cls.table_date_fmt)
        return month_text

    @classmethod
    def get_sharding(cls, shanrding_datetime: datetime.datetime = None):  # type: () -> cls
        shanrding_datetime = shanrding_datetime or datetime.datetime.now()
        return super().get_sharding(shanrding_datetime.strftime(cls.table_date_fmt))
