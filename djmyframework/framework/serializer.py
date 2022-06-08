# -*- coding: utf-8 -*-
# @Time    : 2019-09-09 15:42
# @Author  : xzr
# @File    : serializer
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

import copy
import datetime
from collections.abc import Mapping

from django.db import models

from django.utils.translation import gettext_lazy as _
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers as s
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty, SkipField
from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import ManyRelatedField, RelatedField, PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.settings import api_settings
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework_recursive.fields import RecursiveField
from .utils import DATETIMEFORMAT, ObjectDict
from .utils.cache import CacheAttribute, CachedClassAttribute

Serializer = s.Serializer


class Undefined(object):
    def __bool__(self):
        return False


undefined = Undefined()


class WritableSerializerReturnDict(ReturnDict):
    serializer = None

    def __get_declared_field(self, key):
        declared_field = undefined
        if self.serializer:
            declared_field = self.serializer.declared_fields.get(key, undefined)
        return declared_field

    def __getattr__(self, key):
        declared_field = self.__get_declared_field(key)
        if declared_field is not undefined:
            value = self.get(declared_field.field_name, undefined)
            return value
        raise AttributeError(key)

    def copy(self):
        return WritableSerializerReturnDict(self, serializer=self.serializer)

    def merge(self, dict_data):
        for k, v in dict_data.items():
            if self.get(k, empty) is empty:
                self[k] = v
        return self

    def __setattr__(self, key, value):
        declared_field = self.__get_declared_field(key)
        if declared_field is not undefined:
            try:
                self[declared_field.field_name] = declared_field.to_internal_value(value)
            except:
                self[declared_field.field_name] = value
            return
        if key != 'serializer':
            self[key] = value
        return super().__setattr__(key, value)

    def __delattr__(self, key):
        declared_field = self.__get_declared_field(key)
        if declared_field is not undefined:
            self.pop(declared_field.field_name, None)
        else:
            return super().__delattr__(key)


class ParamsSerializer(s.Serializer):
    _init_complete = False
    __data = None

    def __init__(self, data=empty, instance=None, valid_exception=True, *argv, **kwargs):
        if isinstance(data, models.Model):
            instance = data
            data = empty
        self.valid_exception = valid_exception
        super().__init__(instance=instance, data=data, *argv, **kwargs)
        self._init_complete = True

    def get_initial(self):
        initial_data = ObjectDict()
        has_initial_data = hasattr(self, 'initial_data') and isinstance(self.initial_data, Mapping)

        for field_name in self.fields.keys():
            field = self.declared_fields.get(field_name)
            if has_initial_data:
                value = field.get_value(self.initial_data)
            else:
                try:
                    value = field.get_default()
                except SkipField:
                    value = empty
            if not field.read_only and value is not empty:
                initial_data[field.field_name] = copy.copy(value)  # 保证 DictField ListDict 类不重复
        return initial_data

    @property
    def params_data(self):  # type: () -> self
        """返回设置的与验证过后的数据"""
        self.validation()
        #self.data.merge(self.initial_data)
        return self.o

    @property
    def o(self):
        # type: () -> self
        # 返回自己 用来代码提示
        return self

    @property
    def object_data(self):
        """
        无需校验参数，直接返回数据对象
        """
        return ObjectDict(self.initial_data)

    def __getattribute__(self, key):
        # 实际返回 data
        if key == 'o':
            return super(ParamsSerializer, self).__getattribute__('data')
        return super(ParamsSerializer, self).__getattribute__(key)

    @CacheAttribute
    def data(self):
        if hasattr(self, 'initial_data'):
            self.is_valid(self.valid_exception)
        ret_data = self.__data or super().data
        return WritableSerializerReturnDict(ret_data, serializer=self)

    def validation(self):
        """返回验证过的数据"""
        self.is_valid(True)
        self.__data = self.validated_data
        return self.o

    @CachedClassAttribute
    def declared_fields(cls):
        """初始定义字段,可改变 field_name"""
        ser_obj = cls()
        _declared_fields = ObjectDict()

        for field_name, field in ser_obj.fields.items():
            _field = cls._declared_fields.get(field_name, field)
            _field.field_name = _field.field_name or field_name
            _declared_fields[field_name] = _field

        return _declared_fields

    def get_set_data(self):
        return self.data

    def to_schema(self):
        simple_meta = SimpleMetadata()
        return simple_meta.get_serializer_info(self)

    @CachedClassAttribute
    def schema(cls):
        return cls().to_schema()


DataSerializer = ParamsSerializer


class ConfigOptionSerializer(ParamsSerializer):

    @CachedClassAttribute
    def option_items(cls):
        return cls.declared_fields

    @CachedClassAttribute
    def default_map(cls):
        return cls().data


class NullDateTimeField(s.DateTimeField):
    """
    空字符串的日期时间类型
    """

    def to_internal_value(self, value):
        if not value:
            return None
        return super(NullDateTimeField, self).to_internal_value(value)


class NullDateField(s.DateField):
    """空字符串的日期类型"""

    def to_internal_value(self, value):
        if not value:
            return None
        return super(NullDateField, self).to_internal_value(value)


class NullChoiceField(s.ChoiceField):
    """空字符串的选项类型"""

    def to_internal_value(self, value):
        if not value:
            return None
        return super(NullChoiceField, self).to_internal_value(value)


class NullIntegerField(s.IntegerField):
    """空字符串的整型类型"""

    def to_internal_value(self, value):
        if not value:
            return 0
        return super(NullIntegerField, self).to_internal_value(value)


class NullBooleanField(s.BooleanField):
    """空字符串的整型类型"""

    def to_internal_value(self, value):
        if not value:
            return None
        return super(NullBooleanField, self).to_internal_value(value)


class BaseModelSerializer(DynamicFieldsMixin, s.ModelSerializer, ParamsSerializer):
    id = s.IntegerField(label=_('id'), required=False)
    create_time = s.DateTimeField(label=_('创建时间'), format=DATETIMEFORMAT, required=False, read_only=True,
                                  allow_null=True, default=datetime.datetime.now)
    update_time = s.DateTimeField(label=_('更新时间'), format=DATETIMEFORMAT, required=False, read_only=True,
                                  allow_null=True)
    _version = s.IntegerField(label=_('内置版本号'), read_only=True, required=False, allow_null=True)

    base_exclude = ['_version']
    has_init_meta_cls = False

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        # Instantiate the superclass normally
        super(BaseModelSerializer, self).__init__(*args, **kwargs)
        self.allow_model_fields = fields

    @CacheAttribute
    def fields(self):
        fields = super(BaseModelSerializer, self).fields
        if self.allow_model_fields is not None:
            # 使用 allow_model_fields 限制 django 查询
            allowed = set(self.allow_model_fields)
            existing = set([f.attname for f in self.Meta.model._meta.fields])
            # existing = set(self.Meta.model.fields_map.keys())
            # existing = set(fields.keys())
            for field_name in existing - allowed:
                fields.pop(field_name, '')
        return fields

    def __new__(cls, *args, **kwargs):
        if not cls.has_init_meta_cls:
            cls.has_init_meta_cls = True
        return super().__new__(cls, *args, **kwargs)

    def save(self, **kwargs):
        self.save_kwargs = kwargs
        super(BaseModelSerializer, self).save(**kwargs)

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        from rest_framework.fields import get_error_detail, set_value
        from collections import OrderedDict
        from django.core.exceptions import ValidationError as DjangoValidationError

        if not isinstance(data, Mapping):
            message = self.error_messages['invalid'].format(
                    datatype=type(data).__name__
            )
            raise ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='invalid')

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)

            try:

                # ManyRelatedField 取消写入数据验证, 防止每次都去查询数据库
                if isinstance(field, ManyRelatedField) and isinstance(field.child_relation,
                                                                      PrimaryKeyRelatedField) and primitive_value is not empty:
                    if not isinstance(primitive_value, (list, tuple)):
                        raise ValidationError()
                    validated_value = [int(i) for i in primitive_value]
                else:
                    validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs[-1:], validated_value)

        if errors:
            raise ValidationError(errors)

        return ret


class EmptySerializer(DataSerializer):
    """空的序列化"""
    pass


class IdSerializer(ParamsSerializer):
    id = s.IntegerField(label='ID', help_text=_('对象ID'), required=False, allow_null=True)


class ListIntField(s.ListField):
    def __init__(self, *args, **kwargs):
        super(ListIntField, self).__init__(child=s.IntegerField(), *args, **kwargs)


class ListStrField(s.ListField):
    def __init__(self, *args, **kwargs):
        super(ListStrField, self).__init__(child=s.CharField(allow_blank=True), *args, **kwargs)


class IdsSerializer(ParamsSerializer):
    ids = s.ListField(label='IDS', child=s.IntegerField(allow_null=True, required=False, ), help_text=_('对象ID列表'),
                      required=True, allow_null=False)


class ParamsPaginationSerializer(ParamsSerializer):
    page = s.IntegerField(help_text=_("查询的页码"), required=False, default=1)
    page_size = s.IntegerField(help_text=_("显示条目数,默认100"), required=False, default=100)
    # fileds = s.CharField(help_text=_("需要查询的字段名,以,号分割"))
    # ordering = s.CharField(help_text=_("排序字段 -xxx 为倒序"))


class PaginationSerializer(ParamsSerializer):
    count = s.IntegerField(label=_('总条目数'))
    # next = s.URLField(label=_('下一页地址'), allow_null=True)
    # previous = s.URLField(label=_('上一页地址'), allow_null=True)
    page = s.IntegerField(label=_('当前页数'))
    page_size = s.IntegerField(label=_('每页显示数量'))
    filter = s.DictField(label=_('查询条件'))
    results = s.ListField()


class ModelFilterSerializer(ParamsSerializer):
    model_class = None
    filter_fields = []


class EditParams(IdSerializer):
    is_copy = s.BooleanField(help_text=_("是否复制"), required=False)


class RequestSerializer(Request):
    params = None


class FilterSerializer(ParamsSerializer):
    pass


class CeleryTaskResultSerializer(ParamsSerializer):
    query_id = s.Serializer(label=_('任务查询ID'), required=False)


class RelationModelIdField(RelatedField):
    """关联字段, ManyToManyField 用"""

    def to_representation(self, value_model_list):
        return [value.pk for value in value_model_list]

# class OrgReqSer(DataSerializer):
#     """组织"""
#     organization = IdSerializer(label=_('组织id'), required=True)

class TreeSerializer(DataSerializer):
    key = s.CharField(label=_('键'))
    name = s.CharField(label=_('名称'))
    parent = s.CharField(label=_('父级键'))
    children = s.ListField(label=_('递归本对象'), required=False, read_only=True,
                           child=RecursiveField(label=_('递归本对象')))