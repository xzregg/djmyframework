# -*- coding: utf-8 -*-
# @Time    : 2021-03-24 16:53
# @Author  : xzr
# @File    : routing
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/[/]?$', consumers.WSkGateWayConsumer.as_asgi()),
]