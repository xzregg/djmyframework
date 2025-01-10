# -*- coding: utf-8 -*-
# @Time : 2020-06-08 10:50
# @Author : xzr
# @File : validators.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc :


from django.core.validators import RegexValidator

from framework.translation import _

# 字母组合
LetterValidator = RegexValidator(r'[\d\w_]+$', _('字母组合,符合^[a-z][\d\w_]+$'))

NumberValidator = RegexValidator(r'[\d]+$', _('纯数字组合'))
# Apk package Name
PageckageNameValidator = RegexValidator(r'^[a-z0-9\.]+$', _('包名,符合xx.xx.xx'))

# PassWordRe = r'^(?![0-9]+$)(?![a-zA-Z]+$)[0-9A-Za-z@\-_\.#]{8,20}$' # 框架原有的正则表达式

PassWordRe = r'^\w{8,20}$'   # 前端使用的正则，使用一致

UserNameRe = r'^\w{5,20}$'

PasswordValidator = RegexValidator(PassWordRe,
                                   _('由数字和字母组成，并且要同时含有数字和字母，且长度要在8-20位之间'))

PhoneValidator = RegexValidator(r'^[\d]{8,11}$', _('需符合11位的手机号'))


if __name__ == '__main__':
    PhoneValidator('123412211322')