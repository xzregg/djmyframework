# -*- coding: utf-8 -*-
# @Time    : 2019-08-28 16:20
# @Author  : xzr
# @File    : __init__
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : settings 基本设置


"""
Django settings for myadmin project.

Generated by 'django-admin startproject' using Django 2.0.13.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""
from __future__ import absolute_import

import pymysql

# 使用 pymysql 替代mysqldb
pymysql.install_as_MySQLdb()
import sys
import os
import jinja2

from django.utils.translation import gettext_lazy as _
from objectdict import sort_set_list
from django.conf import settings

DEBUG = True
SECRET_KEY = 'sub6!jx!fuo+%lugsjabk0=il21grymbqwx0-+v5psvb=itq#$'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APPS_ROOT = os.path.join(BASE_DIR, 'apps')
PROJECT_ROOT = BASE_DIR

APPS = ['myadmin', 'analysis', 'celery_task_result', 'log_def', 'upload', 'sync_model', 'ws_gateway']
APPS += ['ldap_account']
sys.path = sort_set_list([settings.BASE_DIR, settings.APPS_ROOT, PROJECT_ROOT, APPS_ROOT] + sys.path)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

TITLE = _('管理后台')

VERSION = 'v3.7'
RELEASE = '01'

ROOT_URLCONF = 'urls'

LOGIN_URL = '/myadmin/login'

INDEX_URL = '/'
INDEX_VIEW = 'myadmin.views.index'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = settings.DEBUG
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ["*"]
AUTH_USER_MODEL = 'myadmin.User'

APPS = sort_set_list(APPS + settings.APPS)

INSTALLED_APPS = ['djorm_pool',
                  'framework',
                  'channels',
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'django_user_agents',
                  'django_filters',
                  'rest_framework',
                  'django_celery_results',
                  'drf_yasg',
                  'django_extensions'
                  ] + APPS

# from rest_framework.views import APIView
# from rest_framework.renderers import JSONRenderer

############ REST_FRAMEWORK设置 ########
REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES'      : [
                # 这里顺序不要更换
                'rest_framework.renderers.TemplateHTMLRenderer',
                'framework.renderers.JSONRenderer'
        ],
        'DEFAULT_SCHEMA_CLASS'          : 'rest_framework.schemas.coreapi.AutoSchema',
        'EXCEPTION_HANDLER'             : 'framework.middleware.exception_handler',
        'DEFAULT_AUTHENTICATION_CLASSES': ('framework.authentication.MySessionAuthentication',)
}
DRF_DYNAMIC_FIELDS = {'SUPPRESS_CONTEXT_WARNING': True}
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')
#######################################


############# channels 配置 #############
CHANNEL_LAYERS = {
        "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG" : {
                        "hosts": ["redis://:123456@10.19.200.185:6379/2"],
                },
        },
}
########################################

############# 数据库连接池 配置 #############
DJORM_POOL_OPTIONS = {
        "pool_size"   : 5,
        "max_overflow": 0,
        "recycle"     : 3600,  # the default value
}
########################################

# session引擎设置
# SESSION_ENGINE='django.contrib.sessions.backends.cache'
# SESSION_COOKIE_AGE = 60 * 30  # 30分钟
# SESSION_SAVE_EVERY_REQUEST = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 关闭浏览器，则COOKIE失效

############# CELERY 配置 #############
# https://docs.celeryproject.org/en/v5.0.5/userguide/configuration.html
CELERY_TIMEZONE = 'Asia/Shanghai'  # 并没有北京时区，与DJANGO TIME_ZONE应该一致
CELERY_BROKER_URL = 'redis://:123456@10.19.200.185:6379/1'
CELERY_RESULT_BACKEND = 'django-db'
# CELERY_CACHE_BACKEND = 'django-cache'
## 异步任务发送最大重试次数,redis 任务发送错误,重试次数
CELERY_BROKER_TRANSPORT_OPTIONS = {'max_retries'   : 3,
                                   "interval_start": 0,
                                   "interval_step" : 0.5,
                                   "interval_max"  : 3  # 最大 sleep 秒数量
                                   }
DJANGO_CELERY_BEAT_TZ_AWARE = False
########################################


############# api 文档设置 ##############

SWAGGER_SETTINGS = {
        # https://drf-yasg.readthedocs.io/en/stable/security.html
        'USE_SESSION_AUTH'         : True,
        # 'DEFAULT_INFO'             : 'settings.API_INFO',
        'DEFAULT_AUTO_SCHEMA_CLASS': 'framework.schema.CustomSwaggerAutoSchema',
}
########################################

X_FRAME_OPTIONS = 'SAMEORIGIN'
MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        # 'django.middleware.csrf.CsrfViewMiddleware',
        # 'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django_user_agents.middleware.UserAgentMiddleware',
        'framework.middleware.BaseMiddleware',
        'myadmin.middleware.AuthMiddleware'
]

# from django.template.context_processors import request
# from django.template.backends.jinja2 import Jinja2
TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'jinja2_templates')

TEMPLATES = [

        {
                'BACKEND' : 'framework.jinja2_env.TemplateJinja2Backend',
                'DIRS'    : [os.path.join(settings.BASE_DIR, 'jinja2_templates')],
                'APP_DIRS': True,
                'OPTIONS' : {
                        'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.i18n',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                                'framework.context_processors.context_settings'
                        ],
                        'environment'       : 'framework.jinja2_env.environment',
                        'undefined'         : jinja2.Undefined
                },
        },
        {
                'BACKEND' : 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS' : {
                        'context_processors': [
                                'django.template.context_processors.debug',
                                'django.template.context_processors.i18n',
                                'django.template.context_processors.request',
                                'django.contrib.auth.context_processors.auth',
                                'django.contrib.messages.context_processors.messages',
                        ],
                },
        },
]

WSGI_APPLICATION = 'wsgi.application'
ASGI_APPLICATION = 'asgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
        {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
]

# 密码加密策略,使用ldap
PASSWORD_HASHERS = [
        'framework.authentication.LDAPSHA1PasswordHasher',
]
# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'zh-hans'
LANGUAGES = (
        ('de', _('German')),
        ('en', _('English')),
        ('zh-hans', _('简体')),
        ('zh-hant', _('繁体')),
)
TIME_ZONE = 'Asia/Shanghai'
LOCALE_PATHS = [os.path.join(settings.BASE_DIR, 'locale'), os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True

USE_L10N = True

USE_TZ = False

# https://docs.djangoproject.com/en/2.0/howto/static-files/https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_DIR = os.path.join(settings.BASE_DIR, 'static/')
STATIC_URL = '/static/'
STATIC_ROOT = STATIC_DIR
# MEDIA_ROOT = STATIC_DIR
MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'media/')

BASE_DIR = settings.BASE_DIR
SECRET_KEY = settings.SECRET_KEY
APPS_ROOT = settings.APPS_ROOT

######### 环境判断 #########
if os.environ.get('DJANGO_ENV', 'dev') == 'dev' and settings.DEBUG:
    from config.dev import *
else:
    from config.prod import *
###########################

from config.logging_config import LOGGING