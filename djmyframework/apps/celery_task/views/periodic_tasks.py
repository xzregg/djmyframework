# -*- coding: utf-8 -*-
# @Time: 2021-04-10 12:12:24.297882


from drf_yasg.utils import swagger_auto_schema
from framework.filters import MyFilterBackend, OrderingFilter, MyFilterSerializer
from framework.translation import _
from framework.route import Route
from framework.serializer import s,BaseModelSerializer, EditParams, IdSerializer, IdsSerializer, ParamsSerializer, PaginationSerializer
from framework.views import CurdViewSet, ListPageNumberPagination, Response,action,Request
from framework.views import render_to_response as rt
from celery_task.models import PeriodicTasks


class PeriodicTasksSerializer(BaseModelSerializer):
    # https://www.django-rest-framework.org/api-guide/serializers/
    # https://www.django-rest-framework.org/api-guide/relations/

    class Meta:
        model = PeriodicTasks
        fields =  ['id', 'ident', 'last_update', 'create_datetime', 'update_datetime'] or '__all__'
        #exclude = ['session_key']
        read_only_fields = ['create_datetime', 'update_datetime']
        #extra_kwargs = {'password': {'write_only': True}}


class ListPeriodicTasksRspSerializer(PaginationSerializer):
    results = PeriodicTasksSerializer(many=True)

@Route('celery_task/periodic_tasks')
class PeriodicTasksSet(CurdViewSet):
    filter_backends = (MyFilterBackend,OrderingFilter)

    serializer_class = PeriodicTasksSerializer
    # 可条件过滤的字段
    filter_fields =  ['id', 'ident', 'last_update', 'create_datetime', 'update_datetime']
    # 可排序的字段
    ordering_fields = ['id', 'ident', 'last_update', 'create_datetime', 'update_datetime']
    # 可以查询字段
    queryset_fields = ['id', 'ident', 'last_update', 'create_datetime', 'update_datetime']

    model = PeriodicTasks

    def get_queryset(self):
        return PeriodicTasks.objects.all().prefetch_related(*[]).select_related(*[]).only(*PeriodicTasksSet.queryset_fields)

    @swagger_auto_schema(query_serializer=MyFilterSerializer,responses=ListPeriodicTasksRspSerializer)
    def list(self, request):
        """PeriodicTasks 列表"""
        return rt("celery_task/periodic_tasks/list.html",super().list(request))

    @swagger_auto_schema(query_serializer=EditParams, responses=PeriodicTasksSerializer)
    def edit(self, request):
        """PeriodicTasks 编辑"""
        return rt("celery_task/periodic_tasks/edit.html",super().edit(request))

    @swagger_auto_schema(query_serializer=IdSerializer,request_body=PeriodicTasksSerializer, responses=PeriodicTasksSerializer)
    def save(self, request):
        """PeriodicTasks 保存"""
        return super().save(request)

    @swagger_auto_schema(request_body=IdsSerializer, responses=IdsSerializer)
    def delete(self, request):
        """PeriodicTasks 删除"""
        return super().delete(request)


    # @swagger_auto_schema(methods=['post'], request_body=PeriodicTasksSerializer, responses=PeriodicTasksSerializer)
    # @action(['post'])
    # def foo_action(self, request):
    #     return Response(PeriodicTasksSerializer().data)