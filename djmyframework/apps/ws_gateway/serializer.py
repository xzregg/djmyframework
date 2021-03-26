# -*- coding: utf-8 -*-
# @Time    : 2019-09-09 15:42
# @Author  : xzr
# @File    : serializer
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

from framework.serializer import DataSerializer, s
from framework.translation import _
from framework.utils.myenum import Enum


class ModelEventActions(Enum):
    SAVE = 'save', _('保存')
    DELETE = 'delete', _('删除')
    SUBSCRIBE = 'subscribe', _('订阅事件')


class ModelEventDataSer(DataSerializer):
    type = s.CharField(label=_('事件类型'), max_length=24,required=False)
    action = s.ChoiceField(label=_('事件'), choices=ModelEventActions.member_list(),required=False)
    model = s.CharField(label=_('模型名称'), max_length=24,required=False)
    data = s.DictField(label=_('数据'),required=False)
    req_id = s.IntegerField(label=_('请求ID'),default=0,required=False)
