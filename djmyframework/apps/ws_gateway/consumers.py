# -*- coding: utf-8 -*-
# @Time    : 2021-03-24 16:51
# @Author  : xzr
# @File    : consumers
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : https://channels.readthedocs.io/en/stable/topics/routing.html#channelnamerouter

import logging

from channels.generic.websocket import JsonWebsocketConsumer,AsyncJsonWebsocketConsumer

logger = logging.getLogger('uvicorn.access')
from asgiref.sync import async_to_sync
from .serializer import ModelEventDataSer, ModelEventActions


class WSkGateWayConsumer(JsonWebsocketConsumer):
    join_groups = set()
    req_id = 0

    def join_to_group(self, group_name):
        logger.info('%s join %s' % (self.channel_name, group_name))
        self.join_groups.add(group_name)
        async_to_sync(self.channel_layer.group_add)(group_name, self.channel_name)

    def leave_groups(self):
        for group_name in self.join_groups:
            async_to_sync(self.channel_layer.group_discard)(group_name, self.channel_name)

    def connect(self):
        logger.info('%s connect' % self.channel_name)
        self.join_to_group('default')
        self.accept()

    def disconnect(self, close_code):
        self.leave_groups()

    def receive_json(self, event: ModelEventDataSer, **kwargs):
        self.req_id += 1
        event_data = ModelEventDataSer(event)
        event_data.o.req_id = event_data.o.req_id or self.req_id
        if event_data.o.action == ModelEventActions.SUBSCRIBE:
            if event_data.o.model:
                self.join_to_group(event_data.o.model)
        self.send_json(event_data.data)

    def broadcast_model_signal(self, event_data: ModelEventActions):
        """django 模型 信号"""
        self.send_json(event_data)

    def system_message(self, event):
        print(event)
        self.send_json(event)
