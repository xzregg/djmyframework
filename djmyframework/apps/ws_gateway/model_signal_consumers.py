# -*- coding: utf-8 -*-
# @Time    : 2021-03-24 16:51
# @Author  : xzr
# @File    : consumers
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : https://channels.readthedocs.io/en/stable/topics/routing.html#channelnamerouter

import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger('uvicorn.access')

from .serializer import ModelEventDataSer, ModelEventActions
from django.apps import apps

class ModelSignalConsumer(AsyncJsonWebsocketConsumer):
    join_groups = set()
    req_id = 0
    allow_groups_map = dict([(m.get_table_name(),m) for m in apps.get_models() if  hasattr(m,'get_table_name')] )


    async def join_to_group(self, group_name):
        logger.info('%s %s join %s' % (str(self.scope['client']),self.channel_name, group_name))
        self.join_groups.add(group_name)
        await self.channel_layer.group_add(group_name, self.channel_name)

    async def leave_groups(self):
        for group_name in self.join_groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def connect(self):
        logger.info('%s connect' % self.channel_name)
        user = self.scope['user']
        if user.is_authenticated:
            await self.join_to_group('default')
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.leave_groups()

    async def receive_json(self, event: ModelEventDataSer, **kwargs):
        self.req_id += 1
        event_data = ModelEventDataSer(event)
        event_data.o.req_id = event_data.o.req_id or self.req_id
        if event_data.o.action == ModelEventActions.SUBSCRIBE:
            if self.allow_groups_map.get(event_data.o.model,None):
                await self.join_to_group(event_data.o.model)
        await self.send_json(event_data.data)

    async def broadcast_model_signal(self, event_data: ModelEventActions):
        """django 模型信号响应"""
        await self.send_json(event_data)

    async def system_message(self, event):

        await self.send_json(event)
