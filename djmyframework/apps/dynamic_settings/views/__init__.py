# -*- coding: utf-8 -*-

from framework.route import Route
from framework.views import api_get, api_post, render_to_response, Request, Response,notauth,action_get,action_post
from ..conf import SettingOptionsManager


@Route
@api_get
def list(request: Request):
    """动态配置"""
    data = SettingOptionsManager().group_options_map
    return render_to_response('dynamic_settimgs/list.html', data, request=request)


@Route
@api_post
def save(request: Request):
    """保存动态配置"""
    settings_data = request.data.get('settings_data', {})
    if settings_data:
        sm = SettingOptionsManager()
        for k, v in settings_data.items():
            sm.set_value(k, v)
    return Response()
