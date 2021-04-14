# -*- coding: utf-8 -*-
# @Time    : 2021-04-14 11:16
# @Author  : xzr
# @File    : test_settingOptions
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

from . import BaseTestCase
from ..conf import Etcd3SettingsBackend, SettingOptions,settings


class TestSettingOptions(BaseTestCase):
    pass

    def test_etcd3(self):
        ec = Etcd3SettingsBackend()
        ec.set_value('tt', 1)
        ec.set_value('asd1', 'asd')
        ec.set_value('asd2', [3, 4, 23])
        ec.set_value('asd3', {2: 3, "asd": 4})
        self.assertEqual(1, ec.get_value('tt'))

    def test_settings(self):
        class A(object):
            c = SettingOptions('b', 'alias')

        S1 = SettingOptions('s1', 'test setttings1', 'S1', 'group1', [(2, 3)])
        S2 = SettingOptions('s2', 'test setttings1', 'S2', 'group1', [(2, 3)])

        S1.set_value('123')
        S2.set_value([1, 3, 32])

        S1.get_value()
        S2.get_value()
        self.assertEqual('123', S1.get_value())
        self.assertEqual([1, 3, 32], S2.get_value())


    def test_system_settings(self):
        from settings import INDEX_URL
        from framework.conf import settings
        settings.INDEX_URL
        from myadmin.settings import LDAP_HOST
        print(LDAP_HOST)