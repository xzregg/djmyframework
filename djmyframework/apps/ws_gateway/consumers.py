# -*- coding: utf-8 -*-
# @Time    : 2021-03-24 16:51
# @Author  : xzr
# @File    : consumers
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

import json

from channels.generic.websocket import WebsocketConsumer


class WSkGateWayConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
                'message': message
        }))
