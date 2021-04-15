# -*- coding: utf-8 -*-
# @Time    : 2021-04-14 11:16
# @Author  : xzr
# @File    : test_settingOptions
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

from unittest import TestCase


class TestSettingOptions(TestCase):

    def test_cls(self):
        class Parent(object):
            def __init__(self):
                self.p = 1

            def __bool__(self):
                return 1

            def pp(self):
                print('pp')
                return self.p

        class A(str,Parent):
            def f1(self):

                return 'f1'

        B=type('cc',(Parent,int),{})

        a=B()
        if a:
            print(3)
        print(type(a))
        print(isinstance(a,int))
        print(a.p)
        print(a.pp())
