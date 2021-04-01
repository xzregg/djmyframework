# -*- coding: utf-8 -*-
# @Time    : 2020-07-16 14:25
# @Author  : xzr
# @File    : settings
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :


AUTH_USER_MODEL = 'myadmin.models.user.User'



class SMS_CONFIG:
    AppKey = '1400029142'
    AppSecret = '122424d328d272fa85cc01d874fa5066'
    sms_free_sign_name = "游娱"
    sms_template_code = "16858"


from settings import *