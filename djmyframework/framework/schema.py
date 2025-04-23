# -*- coding: utf-8 -*-
# @Time    : 2019-09-11 17:17
# @Author  : xzr
# @File    : schema
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :
import copy
import functools
import inspect
import logging
import traceback
from collections import OrderedDict
from functools import lru_cache

import coreschema
from django.urls import resolve
from drf_yasg import openapi
from drf_yasg.errors import SwaggerGenerationError
from drf_yasg.inspectors.field import FieldInspector
from drf_yasg.inspectors.view import SwaggerAutoSchema
from drf_yasg.utils import force_serializer_instance, guess_response_status, no_body, param_list_to_odict, \
    force_real_str
from rest_framework import serializers, status
from rest_framework.relations import ManyRelatedField, RelatedField

from .response import RspErrorEnum, RspSerializer
from .serializer import ModelFilterSerializer
from .utils import ObjectDict
import addict
from .utils.myenum import Enum
from functools import wraps

_api_info = openapi.Info(
        title="Myadmin API",
        default_version='v1',
        description="Myadmin description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License")
)


def compose_enum_description(enum_item_list):
    return '\n'.join([' * `%s` : "%s"  ' % (k, v) for k, v in enum_item_list])


def to_method_title(pathname):
    return ''.join(
            [n.title() if i > 1 else n for i, n in enumerate(pathname.replace('_', '/').split('/'))])


class CustomChoicesFieldInspector(FieldInspector):
    """
    自定选择列表字段描述检测器
    """

    def process_result(self, result, method_name, obj, **kwargs):
        serializer = obj

        # 增加 枚举描述提示,关联模型不执行
        if isinstance(serializer, (ManyRelatedField, RelatedField)):
            return result
        choices_attr = getattr(serializer, 'choices', None)
        if choices_attr:
            enum_item_list = list(serializer.choices.items())

            if not hasattr(result, 'has_add_enum_desc'):
                choices_text = compose_enum_description(enum_item_list)
                setattr(result, 'description', '%s\n%s ' % (getattr(result, 'description', ''), choices_text))
                setattr(result, 'has_add_enum_desc', True)
        return result

def cache_decorator(cache_key):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self._cache[self.path].get(cache_key):
                self._cache[self.path][cache_key] = func(self, *args, **kwargs)
            return self._cache[self.path][cache_key]

        return wrapper

    return decorator

class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    _cache = {}

    def __init__(self, view, path, method, components, request, overrides, operation_keys=None):
        overrides['field_inspectors'] = [CustomChoicesFieldInspector]
        # overrides['filter_inspectors'] = [CustomChoicesFieldInspector]
        super(CustomSwaggerAutoSchema, self).__init__(view, path, method, components, request, overrides,
                                                      operation_keys)
        if self.path not in self._cache:
            self._cache[self.path] = addict.Addict()

    @cache_decorator('summary')
    def get_summary_and_description(self):
        """描述信息"""
        summary, description = super().get_summary_and_description()
        summary_split = description.split(maxsplit=1)
        summary = force_real_str(summary_split[0][:10]) if summary_split else summary
        if summary:
            operation_id = self.get_operation_id()
            url_name = operation_id
            if url_name in description:
                description = description.replace(url_name, '')
            description = f'{url_name}\n{description}'
            summary = '%s %s' % (force_real_str(summary), to_method_title(self.path))

        return summary, description

    def get_app_name(self):
        return self.view.__module__.split('.')[0]

    def filter_request_apps(self):
        result = False
        if self.request:
            filter_apps_text = self.request.GET.get('apps', '')
            is_exclude = self.request.GET.get('is_exclude', '')
            filter_summary_text = self.request.GET.get('summary', '')  # 通过summary过滤
            filter_tags_text = self.request.GET.get('tags', '')  # 通过tags过滤
            filter_path_text = self.request.GET.get('path', '')  # 通过tags过滤
            if filter_apps_text:
                filter_apps = filter_apps_text.split(',')
                app_name = self.get_app_name()
                if filter_apps:
                    result = (app_name not in filter_apps)
            if filter_tags_text:
                filter_tags = filter_tags_text.split(',')
                tags_text = self.overrides.get('tags', [''])[0]
                if tags_text:
                    result = not any(s in tags_text for s in filter_tags)
            if filter_summary_text:
                summary, description = self.get_summary_and_description()
                result = not ((summary and filter_summary_text in summary) or (description and filter_summary_text in description))
            if filter_path_text:
                result = not (self.path and filter_path_text.find(filter_path_text) >= 0)
            if is_exclude:
                result = not result
        return result

    def get_operation(self, operation_keys=None):
        if self.filter_request_apps():
            return None
        # 只返回有 swagger_auto_schema 装饰器的方法
        action = getattr(self.view, 'action', self.method.lower())
        action_method = getattr(self.view, action, None)
        has_decorator_swagger_auto_schema = getattr(action_method, '_swagger_auto_schema', None)
        if not has_decorator_swagger_auto_schema:
            return None
        # 只有设置了参数才返回
        try:
            if self.get_query_serializer() or self.get_request_serializer():
                return super(CustomSwaggerAutoSchema, self).get_operation(operation_keys)
        except Exception as e:
            traceback.print_exc()
            print(f'  {self.path} 定义 {self.method} Serializer 错误!')


    def get_responses(self):
        """Get the possible responses for this view as a swagger :class:`.Responses` object.

        :return: the documented responses
        :rtype: openapi.Responses
        """
        response_serializers = self.get_response_serializers()
        return openapi.Responses(
                responses=self.get_response_schemas(response_serializers)
        )

    @cache_decorator('operation_id')
    def get_operation_id(self, operation_keys=None):
        """Return an unique ID for this operation. The ID must be unique across
        all :class:`.Operation` objects in the API.

        :param tuple[str] operation_keys: an array of keys derived from the pathdescribing the hierarchical layout
            of this view in the API; e.g. ``('snippets', 'list')``, ``('snippets', 'retrieve')``, etc.
        :rtype: str
        """
        try:
            url_name = resolve(self.path).url_name
            return url_name
        except Exception:
            operation_id = super().get_operation_id(operation_keys)
            return operation_id

    def get_view_action(self):
        return getattr(self.view, 'action', '')

    def get_view_annotations(self):
        action_func = self.view
        action_name = self.get_view_action()
        if action_name:
            action_func = getattr(self.view, action_name)
        view_annotations = getattr(action_func, '__annotations__', {})
        return view_annotations

    def get_view_annotations_serializer(self, key):
        serializer = self.get_view_annotations().get(key, None)
        if serializer:
            self.set_serializer_ref_name(serializer)
            return force_serializer_instance(serializer)
        return serializer


    def get_request_serializer(self):
        """Return the request serializer (used for parsing the request payload) for this endpoint.

        :return: the request serializer, or one of :class:`.Schema`, :class:`.SchemaRef`, ``None``
        :rtype: rest_framework.serializers.Serializer
        """

        params_serializer = self.get_view_annotations_serializer('params')
        body_override = self._get_request_body_override() or params_serializer
        #  return body_override
        # if body_override is None and self.method in self.implicit_body_methods:
        #    return self.get_view_serializer()

        if body_override is no_body:
            return None
        self.set_serializer_ref_name(body_override)
        return body_override

    def _get_request_body_override(self):
        """Parse the request_body key in the override dict. This method is not public API."""
        body_override = self.overrides.get('request_body', None)

        if body_override is not None:
            if body_override is no_body:
                return no_body
            # if self.method not in self.body_methods:
            #     raise SwaggerGenerationError("request_body can only be applied to (" + ','.join(self.body_methods) +
            #                                  "); are you looking for query_serializer or manual_parameters?")
            if isinstance(body_override, openapi.Schema.OR_REF):
                return body_override
            return force_serializer_instance(body_override)

        return body_override

    @cache_decorator('query_serializer')
    def get_query_serializer(self):
        """Return the query serializer (used for parsing query parameters) for this endpoint.

        :return: the query serializer, or ``None``
        """
        params_serializer = self.get_view_annotations_serializer('params')
        query_serializer = self.overrides.get('query_serializer', None) or params_serializer
        if query_serializer is not None:
            self.set_serializer_ref_name(query_serializer)
            query_serializer = force_serializer_instance(query_serializer)
        return query_serializer

    def coreapi_field_to_parameter(self, field, in_=openapi.IN_QUERY):
        """Convert an instance of `coreapi.Field` to a swagger :class:`.Parameter` object.

        :param coreapi.Field field:
        :rtype: openapi.Parameter
        """
        location_to_in = {
                'query': openapi.IN_QUERY,
                'path' : openapi.IN_PATH,
                'form' : openapi.IN_FORM,
                'body' : openapi.IN_FORM,
        }
        coreapi_types = {
                coreschema.Integer: openapi.TYPE_INTEGER,
                coreschema.Number : openapi.TYPE_NUMBER,
                coreschema.String : openapi.TYPE_STRING,
                coreschema.Boolean: openapi.TYPE_BOOLEAN,
        }

        coreschema_attrs = ['format', 'pattern', 'enum', 'min_length', 'max_length']
        schema = field.schema
        return openapi.Parameter(
                name=field.name,
                # in_=location_to_in[field.location],
                in_=in_,
                required=field.required,
                description=force_real_str(schema.description) if schema else None,
                type=coreapi_types.get(type(schema), openapi.TYPE_STRING),
                **OrderedDict((attr, getattr(schema, attr, None)) for attr in coreschema_attrs)
        )

    def _get_ref_name(self, serializer):
        app_name = serializer.__module__.replace('.', '_').replace('_serializer_', '_')
        serializer_name = getattr(serializer, '__name__', None) or type(serializer).__name__
        ref_name = f'{app_name}_{serializer_name}'
        return ref_name

    # 设置序列化 ref_name
    def set_serializer_ref_name(self, serializer):
        if serializer:
            serializer_meta = getattr(serializer, 'Meta', None)
            if not serializer_meta:
                setattr(serializer, 'Meta', ObjectDict())

            serializer_meta = getattr(serializer, 'Meta', None)
            ref_name = getattr(serializer_meta, 'ref_name', '')
            real_ref_name = self._get_ref_name(serializer)
            if ref_name != real_ref_name:
                setattr(serializer_meta, 'ref_name', real_ref_name)

        return serializer

    def get_request_body_parameters(self, consumes):

        parameters = super().get_request_body_parameters(consumes)
        serializer = self.get_request_serializer()
        self.set_serializer_ref_name(serializer)
        return parameters + self.get_myfilter_parameters(serializer, openapi.IN_BODY)

    def get_request_body_schema(self, serializer):
        schemas = super().get_request_body_schema(serializer)
        return schemas

    def get_myfilter_parameters(self, serializer, in_=openapi.IN_QUERY):
        if isinstance(serializer, ModelFilterSerializer):
            from .filters import MyFilterBackend
            serializer_parameters_fields = MyFilterBackend().get_schema_fields_from_model(serializer.model_class,
                                                                                          serializer.filter_fields)
            serializer_parameters = [self.coreapi_field_to_parameter(field) for field in
                                     serializer_parameters_fields]
            return serializer_parameters
        return []


    def get_query_parameters(self):
        """Return the query parameters accepted by this view.

        :rtype: list[openapi.Parameter]
        """

        natural_parameters = self.get_filter_parameters() + self.get_pagination_parameters()

        # natural_parameters = []

        query_serializer = self.get_query_serializer()

        serializer_parameters = []
        self.set_serializer_ref_name(query_serializer)
        if query_serializer is not None:
            filter_parameters = self.get_myfilter_parameters(query_serializer, in_=openapi.IN_QUERY)
            serializer_parameters = self.serializer_to_parameters(query_serializer, in_=openapi.IN_QUERY)
            # if serializer_parameters:
            return serializer_parameters + filter_parameters
            if len(set(param_list_to_odict(natural_parameters)) & set(param_list_to_odict(serializer_parameters))) != 0:
                raise SwaggerGenerationError(
                        "your query_serializer contains fields that conflict with the "
                        "filter_backend or paginator_class on the view - %s %s" % (self.method, self.path)
                )

        return natural_parameters + serializer_parameters


    def get_response_serializers(self):
        """Return the response codes that this view is expected to return, and the serializer for each response body.
        The return value should be a dict where the keys are possible status codes, and values are either strings,
        ``Serializer``\\ s, :class:`.Schema`, :class:`.SchemaRef` or :class:`.Response` objects. See
        :func:`@swagger_auto_schema <.swagger_auto_schema>` for more details.

        :return: the response serializers
        :rtype: dict
        """

        manual_responses = self.overrides.get('responses', None) or self.get_view_annotations_serializer('return')
        if not isinstance(manual_responses, dict):
            manual_responses = {status.HTTP_200_OK: manual_responses}
        responses = OrderedDict(
                (str(sc), self.generate_rsp_serializer_schema(resp)) for sc, resp in manual_responses.items())

        return responses

    def generate_rsp_serializer_schema(self, rsp_data_serializer: serializers.Field = None):
        """
        生成最终 rsp 结果,添加 错误代码描述
        :param rsp_serializer:
        :return:
        """

        if rsp_data_serializer:
            self.set_serializer_ref_name(rsp_data_serializer)
            rep_code_errors: RspErrorEnum = getattr(rsp_data_serializer, 'Errors', None) or getattr(rsp_data_serializer, 'RspCode', None)
            default_declared_fields = RspSerializer._declared_fields
            rep_code_serializer = default_declared_fields['code']
            choices = rep_code_serializer.choices
            # 增加错误代码
            if rep_code_errors and (issubclass(rep_code_errors, (RspErrorEnum, Enum)) or isinstance(rep_code_errors, (RspErrorEnum, list, tuple, Enum))):
                if hasattr(rep_code_errors, 'member_list'):
                    rsp_err_code_member_list = rep_code_errors.member_list()
                choices = copy.copy(rep_code_serializer.choices)
                choices.update(rsp_err_code_member_list)
            choices = list(choices.items())
            rsp_code_schema = self.serializer_to_schema(
                    serializers.ChoiceField(label=rep_code_serializer.label, choices=choices))

            rsp_data_serializer = force_serializer_instance(rsp_data_serializer)
        else:
            rsp_code_schema = self.serializer_to_schema(RspSerializer._declared_fields['code'])
            rsp_data_serializer = RspSerializer._declared_fields['data']

        default_schema = openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties=OrderedDict(
                        (
                                ('code', rsp_code_schema),
                                ('msg', self.serializer_to_schema(RspSerializer._declared_fields['msg'])),
                                ('data', self.serializer_to_schema(rsp_data_serializer))
                        )
                ),
                required=['code', 'msg']
        )

        return default_schema

    def _get_default_responses(self):
        """Get the default responses determined for this view from the request serializer and request method.

        :type: dict[str, openapi.Schema]
        """
        method = self.method.lower()

        default_status = guess_response_status(method)

        default_schema = self.get_default_response_serializer()

        default_schema = default_schema or ''
        if default_schema and not isinstance(default_schema, openapi.Schema):
            default_schema = self.serializer_to_schema(default_schema) or ''

        if default_schema and self.get_view_action() not in ('edit'):
            if self.has_list_response():
                default_schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=default_schema)
            if self.should_page():
                query_schema = self.get_query_serializer() or serializers.DictField(help_text="查询条件", required=False)
                paged_schema = openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties=OrderedDict((
                                ('count', openapi.Schema(type=openapi.TYPE_INTEGER)),
                                ('page', openapi.Schema(type=openapi.TYPE_INTEGER)),
                                ('page_size', openapi.Schema(type=openapi.TYPE_INTEGER)),

                                ('next',
                                 openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, x_nullable=True)),
                                ('previous',
                                 openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, x_nullable=True)),
                                ('results', default_schema),
                                ('filter', self.serializer_to_schema(query_schema)),
                        )),
                        required=['results']
                )
                default_schema = paged_schema

        rsp_code_schema = self.serializer_to_schema(RspSerializer._declared_fields['code'])

        default_schema = openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties=OrderedDict((
                        ('code', rsp_code_schema),
                        ('msg', self.serializer_to_schema(RspSerializer._declared_fields['msg'])),
                        ('data', default_schema)
                )
                ),
                required=['code', 'msg']
        )

        return OrderedDict({str(default_status): default_schema})
