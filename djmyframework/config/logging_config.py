# -*- coding: utf-8 -*-
#
# django logging的配置
#


import os


def get_log_dir():
    from django.conf import settings
    return os.path.join(settings.BASE_DIR, 'logs')


def get_timed_rotating_file_config(dir, filename):
    '''返回一个以日切割的循环日志配置
    '''
    log_dir_path = os.path.join(get_log_dir(), dir)
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path, 0o766)
    return {
            'level'      : 'DEBUG',
            'class'      : 'framework.utils.multiprocesslogging.MultiProcessTimedRotatingFileHandler',
            # 'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter'  : 'format01',
            'filename'   : os.path.join(log_dir_path, filename),
            'when'       : 'H',
            'interval'   : 24,
            'encoding'   : 'utf-8',
            'backupCount': 10,  # 指定保留的备份文件的个数
    }


LOGGING = {
        'version'                 : 1,
        'disable_existing_loggers': False,
        'filters'                 : {
                'require_debug_false': {
                        '()': 'django.utils.log.RequireDebugFalse'
                }
        },
        # =========== handlers start =================
        'handlers'                : {
                'mail_admins'      : {
                        'level'  : 'ERROR',
                        'filters': ['require_debug_false'],
                        'class'  : 'django.utils.log.AdminEmailHandler'
                },
                'console'          : {
                        'level'    : 'DEBUG',
                        'class'    : 'logging.StreamHandler',
                        'formatter': 'format02'
                },
                'root_handler'     : get_timed_rotating_file_config('', 'root.log'),
                'gm_handler'       : get_timed_rotating_file_config('gm', 'gm.log'),
                'pay_handler'      : get_timed_rotating_file_config('pay', 'pay.log'),
                'card_handler'     : get_timed_rotating_file_config('card', 'card.log'),
                'statistic_handler': get_timed_rotating_file_config('statistic', 'statistic.log'),
        },
        # =========== loggers start =================
        'loggers'                 : {
                'django.request'        : {
                        'handlers' : ['root_handler', 'console'],
                        'level'    : 'ERROR',
                        'propagate': False,
                },
                'root'                  : {
                        'qualname' : 'root',
                        'level'    : 'DEBUG',
                        'handlers' : ['root_handler', 'console'],
                        'propagate': False,
                },
                'django.channels.server': {
                        'qualname' : 'root',
                        'level'    : 'DEBUG',
                        'handlers' : ['root_handler', 'console'],
                        'propagate': False,
                },
                'gm'                    : {
                        'qualname' : 'gm',
                        'level'    : 'DEBUG',
                        'handlers' : ['gm_handler'],
                        'propagate': False,
                },
                'pay'                   : {
                        'qualname' : 'pay',
                        'level'    : 'DEBUG',
                        'handlers' : ['pay_handler'],
                        'propagate': False,
                },
                'card'                  : {
                        'qualname' : 'card',
                        'level'    : 'DEBUG',
                        'handlers' : ['card_handler'],
                        'propagate': False,
                },
                'cache'                 : {
                        'qualname' : 'cache',
                        'level'    : 'DEBUG',
                        'handlers' : ['console'],
                        'propagate': False,
                },
                'grpc_server'           : {
                        'qualname' : 'grpc',
                        'level'    : 'DEBUG',
                        'handlers' : ['console'],
                        'propagate': False,  # 是否传递到 root handler
                },
                'statistic'             : {  # 统计日志
                        'qualname' : 'statistic',
                        'level'    : 'DEBUG',
                        'handlers' : ['console', 'statistic_handler'],
                        'propagate': False,
                },
                'uvicorn.access'        : {  # 统计日志
                        'qualname' : 'statistic',
                        'level'    : 'INFO',
                        'handlers' : ['console'],
                        'propagate': False,
                },
                'uvicorn.error'         : {  # 统计日志
                        'qualname' : 'statistic',
                        'level'    : 'ERROR',
                        'handlers' : ['console'],
                        'propagate': False,
                }

        },

        # =========== formatters start ================= https://docs.python.org/2/library/logging.html
        'formatters'              : {
                'format01': {
                        'format' : '%(asctime)s [%(levelname)s] %(name)s pid:%(process)d %(pathname)s:%(lineno)d %(message)s',
                        'datefmt': '[%Y-%m-%dT%H:%M:%S%z]'  # ISO 8601
                },
                'format02': {
                        'format' : '%(asctime)s %(levelname)s %(name)s pid:%(process)d %(filename)s:%(lineno)d %(message)s',
                        'datefmt': '[%Y-%m-%dT%H:%M:%S%z]'
                }

        }
}
