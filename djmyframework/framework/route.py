# -*- coding: utf-8 -*-
# 自动注册 url
import importlib
import logging
import os
import traceback

from django.conf import settings
from django.urls import re_path, reverse
from rest_framework import routers as rest_route
from .utils.myenum import Enum
from .translation import _

APPS_ROOT = settings.APPS_ROOT
from .utils import trace_msg


class CurdType(Enum):
    """增删改查的类型"""
    Add = 'add', _('新增')
    List = 'list', _('查询')
    Edit = 'edit', _('编辑')
    Modify = 'modify', _('编辑')
    Delete = 'delete', _('删除')

class CustomRestRouter(rest_route.DefaultRouter):
    include_format_suffixes = False
    routes = [
            # List route.
            rest_route.Route(
                    url=r'^{prefix}/list$',
                    mapping={
                            'get': 'list',

                    },
                    name='{basename}.list',
                    detail=False,
                    initkwargs={'suffix': 'List'}
            ),
            rest_route.Route(
                    url=r'^{prefix}/save$',
                    mapping={
                            'post': 'save'
                    },
                    name='{basename}.save',
                    detail=True,
                    initkwargs={}
            ),
            rest_route.Route(
                    url=r'^{prefix}/delete$',
                    mapping={
                            'post': 'delete'
                    },
                    name='{basename}.delete',
                    detail=False,
                    initkwargs={}
            ),
            rest_route.Route(
                    url=r'^{prefix}/edit$',
                    mapping={
                            'get': 'edit',
                    },
                    name='{basename}.edit',
                    detail=True,
                    initkwargs={}
            ),
            rest_route.Route(
                    url=r'^{prefix}/metadata$',
                    mapping={
                            'get'    : 'metadata',
                            'options': 'metadata',
                    },
                    name='{basename}.metadata',
                    detail=True,
                    initkwargs={}
            ),
            # Dynamically generated list routes. Generated using
            # @action(detail=False) decorator on methods of the viewset.
            rest_route.DynamicRoute(
                    url=r'^{prefix}/{url_path}$',
                    name='{basename}.{url_name}',
                    detail=False,
                    initkwargs={}
            )
    ]


rest_router = CustomRestRouter()
rest_router.include_root_view = False
VIEWS_DIR = settings.VIEWS_DIR
if not isinstance(VIEWS_DIR, list):
    VIEWS_DIR = [VIEWS_DIR]
GLOBAL_ROUTE_PREFIX = settings.ROUTE_PREFIX
ROUTE_APP_PREFIX_MAP = settings.ROUTE_APP_PREFIX_MAP

Handlers = set()


class Route(object):
    """
    @自动添加django URL
    """

    def __new__(cls, *args, **kwargs):
        ins = super().__new__(cls)
        if len(args) > 0:
            if not isinstance(args[0], str):
                ins.__init__()
                return ins(*args)
        return ins

    def __init__(self, re_url='', name=None, use_global_prefix=True, *args, **kwargs):
        self.re_url = re_url
        self.args = args
        self.kwargs = kwargs
        self.name = name
        self.use_global_prefix = use_global_prefix

    def __call__(self, obj):
        _m = obj.__module__
        p_m_f = '%s.%s' % (_m, obj.__name__)
        for view_dir_name in VIEWS_DIR:
            p_m_f = p_m_f.replace('%s.' % view_dir_name, '', 1).strip('.')
        names = p_m_f.lower().split('.')

        # 重复路径去重
        names_set = list(set(names))
        names_set.sort(key=names.index)

        name = '.'.join(names_set).lower()

        uri = name.replace('.', '/').rstrip('/')
        _doc = obj.__doc__
        view_func = obj

        setattr(obj, 'route_name', name)

        app_name = p_m_f[:p_m_f.find('.')]

        route_prefix = ROUTE_APP_PREFIX_MAP.get(app_name, '')
        if self.use_global_prefix:
            route_prefix = '%s%s' % (GLOBAL_ROUTE_PREFIX, route_prefix)
        # rest_framework GenericViewSet
        if hasattr(obj, 'get_serializer'):
            prefix = self.re_url or uri
            basename = prefix.replace('/', '.').strip('^').strip('$')
            prefix = '%s%s' % (route_prefix, prefix.strip('^'))
            rest_router.register(prefix, obj, basename=basename)
            return obj

        # BaseModelView
        if hasattr(obj, 'deny_method_names'):
            re_path_str = '(?P<path>\w+)'
            if re_path_str not in self.re_url:
                self.re_url = '%s/%s' % (self.re_url, re_path_str)
            setattr(obj, 'url_prefix', '/%s' % '/'.join(self.re_url.strip('^').split('/')[:-1]))
            view_func = obj.as_view()

        if self.re_url == '':
            self.re_url = '%s' % uri
        self.re_url = '%s%s' % (route_prefix, self.re_url.strip('^'))
        if not self.re_url.startswith('^'):
            self.re_url = '^%s' % self.re_url
        if not self.re_url.endswith('$'):
            self.re_url = '%s$' % self.re_url

        _url = re_path(self.re_url, view_func,
                       name=self.name or name,
                       kwargs=self.kwargs)
        _url.__doc__ = _doc
        setattr(_url, 'doc', str(_doc).split('\n')[0])
        setattr(_url, 'group', _m)
        setattr(_url, 'url', self.re_url)
        Handlers.add(_url)
        return obj


def _get_pyfile(dirlist):
    dirlist = [dirlist] if isinstance(dirlist, str) else dirlist
    for _dir in dirlist:
        if os.path.isdir(_dir):
            for dirpath, dirs, files in os.walk(_dir):
                for filename in files:
                    if filename.endswith('.py'):
                        yield filename, os.path.join(dirpath, filename)


def _import_module_from_file():
    from django.conf import settings
    from django.apps import apps
    app_names = settings.APPS
    for app_module_name in app_names:
        app_name = app_module_name  # .rsplit('.')[-1]

        app_config = apps.app_configs.get(app_module_name)
        if not app_config:
            continue
        views_dir_names = VIEWS_DIR
        for views_name in views_dir_names:
            views_dir_path = os.path.join(app_config.path, views_name)

            if os.path.isfile('%s.py' % views_dir_path):
                importlib.import_module('%s.%s' % (app_name, views_name))
            else:
                for filename, pyfile in _get_pyfile(views_dir_path):
                    # view_model_name = filename.replace('__init__', '')[:-3]
                    # _p_m = '.'.join([app_name, VIEWS_DIR, view_model_name]).strip('.')

                    view_model_name = pyfile.replace(app_config.path, '').replace('__init__', '')[:-3].replace(os.path.sep,
                                                                                                               '.').strip(
                            '.')
                    _p_m = '%s.%s' % (app_module_name, view_model_name)

                    try:

                        importlib.import_module(_p_m)
                    except Exception as e:
                        logging.error(trace_msg())


def reverse_view(view_or_name, *args, **kwargs):
    try:
        return reverse(view_or_name, *args, **kwargs)
    except Exception as e:
        traceback.print_exc()
        return ''


def get_urls():
    _import_module_from_file()
    return list(Handlers) + rest_router.get_urls()


get_urlpatterns = get_urls
