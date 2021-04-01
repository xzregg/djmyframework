# -*- coding: utf-8 -*-
# @Time: 2021-04-01 11:40:50.721287


from drf_yasg.utils import swagger_auto_schema
from framework.filters import MyFilterBackend, OrderingFilter, MyFilterSerializer
from framework.translation import _
from framework.route import Route
from framework.serializer import s,BaseModelSerializer, EditParams, IdSerializer, IdsSerializer, ParamsSerializer, PaginationSerializer
from framework.views import CurdViewSet, ListPageNumberPagination, Response,action,Request
from framework.views import render_to_response as rt
from ldap_account.models import AccessDomain


class AccessDomainSerializer(BaseModelSerializer):
    # https://www.django-rest-framework.org/api-guide/serializers/
    # https://www.django-rest-framework.org/api-guide/relations/
    status_alias = s.CharField(source='get_status_display',required=False, read_only=True)

    class Meta:
        model = AccessDomain
        fields =  ['id', 'name', 'alias', 'bindpw','basedn', 'access_address', 'status', 'create_datetime', 'update_datetime', 'status_alias'] or '__all__'
        #exclude = ['session_key']
        read_only_fields = ['create_datetime', 'update_datetime']
        #extra_kwargs = {'password': {'write_only': True}}


class ListAccessDomainRspSerializer(PaginationSerializer):
    results = AccessDomainSerializer(many=True)

@Route('ldap_account/access_domain')
class AccessDomainSet(CurdViewSet):
    filter_backends = (MyFilterBackend,OrderingFilter)

    serializer_class = AccessDomainSerializer
    # 可条件过滤的字段
    filter_fields =  ['id', 'name', 'alias', 'bindpw', 'access_address', 'status', 'create_datetime', 'update_datetime']
    # 可排序的字段
    ordering_fields = ['id', 'name', 'alias', 'bindpw', 'access_address', 'status', 'create_datetime', 'update_datetime']
    # 可以查询字段
    queryset_fields = ['id', 'name', 'alias', 'bindpw', 'access_address', 'status', 'create_datetime', 'update_datetime']

    model = AccessDomain

    def get_queryset(self):
        return AccessDomain.objects.all().prefetch_related(*[]).select_related(*[]).only(*AccessDomainSet.queryset_fields)

    @swagger_auto_schema(query_serializer=MyFilterSerializer,responses=ListAccessDomainRspSerializer)
    def list(self, request):
        """访问域 列表"""
        return rt("ldap_account/access_domain/list.html",super().list(request))

    @swagger_auto_schema(query_serializer=EditParams, responses=AccessDomainSerializer)
    def edit(self, request):
        """访问域 编辑"""
        return rt("ldap_account/access_domain/edit.html",super().edit(request))

    @swagger_auto_schema(query_serializer=IdSerializer,request_body=AccessDomainSerializer, responses=AccessDomainSerializer)
    def save(self, request):
        """访问域 保存"""
        return super().save(request)

    @swagger_auto_schema(request_body=IdsSerializer, responses=IdsSerializer)
    def delete(self, request):
        """访问域 删除"""
        return super().delete(request)


    # @swagger_auto_schema(methods=['post'], request_body=AccessDomainSerializer, responses=AccessDomainSerializer)
    # @action(['post'])
    # def foo_action(self, request):
    #     return Response(AccessDomainSerializer().data)