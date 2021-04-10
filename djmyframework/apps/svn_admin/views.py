# -*- coding: utf-8 -*-
# @Time: 2020-07-07 18:59:41.458233
import os

from drf_yasg.utils import swagger_auto_schema

from framework.filters import MyFilterBackend, MyFilterSerializer, OrderingFilter
from framework.route import Route
from framework.serializer import BaseModelSerializer, EditParams, IdSerializer, IdsSerializer, PaginationSerializer, s
from framework.translation import _
from framework.utils import ObjectDict
from framework.views import action, CurdViewSet, JsonResponse, render_to_response, Response
from svn_admin.models import SvnPath


class SvnPathSerializer(BaseModelSerializer):
    # https://www.django-rest-framework.org/api-guide/serializers/
    # https://www.django-rest-framework.org/api-guide/relations/
    # parent = s.RelatedField(label=_("上级ID"),queryset= SvnPath.parent.field.related_model.objects.all())
    status_alias = s.CharField(source='get_status_display', required=False, read_only=True)
    other_permission_alias = s.CharField(source='get_other_permission_display', required=False, read_only=True)

    def validate_path(self, value):
        if value == '/' and SvnPath.objects.filter(project_name=self.instance.project_name, path='/').exclude(
                id=self.instance.id).exists():
            raise s.ValidationError(_(' 相同 [ %s ] 项目只能有一个 / 根') % self.instance.project_name)
        return value

    class Meta:
        model = SvnPath
        fields = ['id', 'alias', 'project_name', 'path', 'parent', 'status', 'remark', 'read_member', 'write_member',
                  'other_permission', 'create_datetime', 'update_datetime', 'status_alias',
                  'other_permission_alias'] or '__all__'
        # exclude = ['session_key']
        read_only_fields = ['create_datetime', 'update_datetime']
        # extra_kwargs = {'password': {'write_only': True}}


class ListSvnPathRspSerializer(PaginationSerializer):
    results = SvnPathSerializer(many=True)


@Route('svn_admin/svn_path')
class SvnPathSet(CurdViewSet):
    filter_backends = (MyFilterBackend, OrderingFilter)

    serializer_class = SvnPathSerializer
    # 可条件过滤的字段
    filter_fields = ['id', 'alias', 'project_name', 'path', 'parent', 'status', 'remark', 'read_member', 'write_member',
                     'other_permission', 'create_datetime', 'update_datetime']
    # 可排序的字段
    ordering_fields = ['id', 'alias', 'project_name', 'path', 'parent', 'status', 'remark', 'read_member',
                       'write_member', 'other_permission', 'create_datetime', 'update_datetime']

    model = SvnPath

    def get_queryset(self):
        return SvnPath.objects.all().prefetch_related(*[]).select_related(*['parent'])

    @swagger_auto_schema(query_serializer=MyFilterSerializer, responses=ListSvnPathRspSerializer)
    def list(self, request):
        """ 列表"""
        SvnPath.init_svn_projects()
        return render_to_response('svn_admin/svn_path/list.html', super().list(request))

    @swagger_auto_schema(query_serializer=EditParams, responses=SvnPathSerializer)
    def edit(self, request):
        """ 编辑"""
        return render_to_response('svn_admin/svn_path/edit.html', super().edit(request))

    @swagger_auto_schema(query_serializer=IdSerializer, request_body=SvnPathSerializer, responses=SvnPathSerializer)
    def save(self, request):
        """ 保存"""

        return super(SvnPathSet, self).save(request)

    @swagger_auto_schema(request_body=IdsSerializer, responses=IdsSerializer)
    def delete(self, request):
        return super(SvnPathSet, self).delete(request)

    @action('get')
    def svn_project_list(self, request):
        project_list = SvnPath.get_svn_project_list()
        data = ObjectDict()
        data.results = []
        for project_name in project_list:
            data.results.append(dict(id=project_name, alias=project_name))
        return JsonResponse(data)

    @action('get')
    def preview_db_files(self, request):
        from .settings import SVN_AUTH_DB_FILE, SVN_GROUP_DB_FILE
        auth_db_content = open(SVN_GROUP_DB_FILE).read() + open(SVN_AUTH_DB_FILE).read()
        passowrd_db_content = ''  # open(SVN_PASSWORD_DB_FILE).read()
        return Response(locals())

    @action('post')
    def create_svnrepo(self, request):
        """
        创建 SVN 仓库
        :param request:
        :return:
        """
        svnrepo_name = request.POST.get('svnrepo_name', '').strip()
        if svnrepo_name:
            SvnPath.create_svnrepo(svnrepo_name)

        return render_to_response('svn_admin/svn_path/create_svnrepo.html', super().edit(request))


    # @swagger_auto_schema(methods=['post'], request_body=SvnPathSerializer, responses=SvnPathSerializer)
    # @action(['post'])
    # def foo_action(self, request):
    #     return Response(SvnPathSerializer().data)
