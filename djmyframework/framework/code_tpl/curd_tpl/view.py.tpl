# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# @Time: ${datetime}


from framework.filters import MyFilterBackend, OrderingFilter, MyFilterSerializer
from framework.translation import _
from framework.route import Route
from framework.serializer import s,BaseModelSerializer, EditParams, IdSerializer, IdsSerializer, ParamsSerializer, PaginationSerializer
from framework.views import CurdViewSet, ListPageNumberPagination,action,api_doc
from framework.views import render_to_response as rt
from django.db import models
from ${app_name}.models import ${model_name}
from django.db import transaction
from framework.shortcut import APIError,Response,api_doc,api_get,api_post
from ${app_name}.serializer.${model_lower_name} import *
from ${app_name}.service.${model_lower_name} import ${model_name}Service

@Route('${app_name}/${model_lower_name}')
class ${model_name}Set(CurdViewSet):
    """${app_verbose_name} ${model_desc}"""
    filter_backends = (MyFilterBackend,OrderingFilter)

    serializer_class = ${model_name}Serializer
    # 可条件过滤的字段
    filter_fields =  ${list(fields_name_list)}
    # 可排序的字段
    ordering_fields = ${list(fields_name_list)}
    # 可以查询字段
    queryset_fields = ${list(fields_name_list)}

    model = ${model_name}

    service =  ${model_name}Service()

    def get_queryset(self) -> models.Q:
        return ${model_name}.objects.all().prefetch_related(*${[f.name for f in model_many_to_many]}).select_related(*${[f.name for f in model_foreigns]}).only(*${model_name}Set.queryset_fields)

    @api_doc(tags=['${app_verbose_name}'], query_serializer=MyFilterSerializer,responses=List${model_name}RspSerializer)
    def list(self, request):
        """${model_desc} 列表"""
        return rt("${app_name}/${model_lower_name}/list.html",super().list(request))

    @api_doc(tags=['${app_verbose_name}'], query_serializer=EditParams, responses=${model_name}Serializer)
    def edit(self, request):
        """${model_desc} 编辑"""
        return rt("${app_name}/${model_lower_name}/edit.html",super().edit(request))

    @api_doc(tags=['${app_verbose_name}'], request_body=${model_name}Serializer, responses=${model_name}Serializer)
    def add(self, request):
        """${model_desc} 新增"""
        return super().save(request)

    @api_doc(tags=['${app_verbose_name}'], query_serializer=IdSerializer,request_body=${model_name}Serializer, responses=${model_name}Serializer)
    def save(self, request):
        """${model_desc} 保存"""
        return super().save(request)

    @api_doc(tags=['${app_verbose_name}'], request_body=IdsSerializer, responses=IdsSerializer)
    def delete(self, request):
        """${model_desc} 删除"""
        return super().delete(request)


    # @api_doc(methods=['post'], request_body=${model_name}Serializer, responses=${model_name}Serializer)
    # @api_post
    # def foo_action(self, request):
    #     return Response(${model_name}Serializer().data)