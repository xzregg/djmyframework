# -*- coding: utf-8 -*-
# @Time    : 2019-08-28 16:20
# @Author  : xzr
# @File    : __init__
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 开发环境 settings 基本设置


# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True
import logging
import os
import sys
from django.contrib.auth import  authenticate


DEBUG = True

from django.conf import settings
from settings import *

# session引擎设置
# SESSION_ENGINE='django.contrib.sessions.backends.cache'
# SESSION_COOKIE_AGE = 60 * 30  # 30分钟
# SESSION_SAVE_EVERY_REQUEST = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 关闭浏览器，则COOKIE失效


STATICFILES_DIRS = [os.path.join(settings.BASE_DIR, 'static')]
STATIC_ROOT = None
_DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME'  : os.path.join(settings.BASE_DIR, 'sqlite3.db'),
                'TEST'  : {
                        'NAME': os.path.join(settings.BASE_DIR, 'test.db.sqlite3.db')

                }
        },

}

DATABASES = {
        'default': {

                'ENGINE'  : 'django.db.backends.mysql',

                'NAME'    : 'djmyadmin',
                'USER'    : 'root',
                'PASSWORD': '123456',

                'HOST'    : '10.19.200.185',

                'PORT'    : '3306',

                'OPTIONS' : {'isolation_level': None, 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},

        }

}

DATABASES['card'] = DATABASES['default'].copy()

if 'test' in sys.argv:
    # 使用内存数据库加速测试
    DATABASES = {
            'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME'  : ':memory'
            }
    }
    CHANNEL_LAYERS = {
            "default": {
                    "BACKEND": "channels.layers.InMemoryChannelLayer"
            }
    }

DATABASES['read'] = DATABASES['default'].copy()
DATABASES['write'] = DATABASES['default'].copy()

#INSTALLED_APPS += ['debug_toolbar']
INTERNAL_IPS = [
        '*',
        '127.0.0.1'
]

#MIDDLEWARE.insert(len(MIDDLEWARE) - 1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
DEBUG_TOOLBAR_CONFIG = {
        'JQUERY_URL': '',
}

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('framework.renderers.DebugRenderer')
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')
logging.warning('This env is dev,DEBUG = True')
logging.warning('BASE_DIR: %s' % settings.BASE_DIR)


# 日志打印 sql
from . import logging_config
logging_config.LOGGING['loggers']['adjango.db.backends'] = {
        'handlers' : ['console'],
        'propagate': False,
        'level'    : 'DEBUG',
}
