# -*- coding: utf-8 -*-
# @Time    : 2021-03-23 17:59
# @Author  : xzr
# @File    : client
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from framework.serializer import DataSerializer, s
from framework.translation import _
from .settings import WEBSOCKET_SERVERS

class EventDataSer(DataSerializer):
    """时间数据结构"""
    group = s.CharField(label=_('组'), max_length=12, required=False)
    target = s.CharField(label=_('目标'), max_length=64, required=False)
    data = s.DictField(label=_('具体数据'), required=False)



class WebSocketClient(object):
    pass