# -*- coding: utf-8 -*-




import os




_SETTINGS_LOADER_ETCD = dict(host='localhost', port=2379,
                            ca_cert=None, cert_key=None, cert_cert=None, timeout=None,
                            user=None, password=None, grpc_options=None, prefix_key=os.environ.get('DJANGO_ENV', 'dev'))

_SETTINGS_LOADER_REDIS = dict(url='redis://:123456@10.19.200.185:6379/5', decode_responses=True,
                             prefix_key=os.environ.get('DJANGO_ENV', 'dev'))



# 全局配置覆盖项目
from settings import *