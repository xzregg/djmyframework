# -*- coding: utf-8 -*-
# @Time    : 2021-03-24 16:51
# @Author  : xzr
# @File    : consumers
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

import json
from channels.layers import get_channel_layer
from channels.generic.websocket import WebsocketConsumer,JsonWebsocketConsumer
import logging

logger = logging.getLogger('uvicorn.access')
from asgiref.sync import async_to_sync
class WSkGateWayConsumer(JsonWebsocketConsumer):
    def connect(self):
        logger.info('connect')
        async_to_sync(self.channel_layer.group_add)("test", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("test", self.channel_name)

    def receive_json(self, text_data_json):
        logger.info(text_data_json)
        message = text_data_json['message']
        async_to_sync(self.channel_layer.group_send)(
                "test",
                {
                        "type": "system_message",
                        "text": message,
                },
        )


    def system_message(self, event):
        print(event)
        message = event['message']

        # Send message to WebSocket单发消息
        self.send_json({
                'message': message
        })