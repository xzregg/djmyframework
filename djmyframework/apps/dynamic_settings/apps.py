# -*- coding: utf-8 -*-

from django.apps import AppConfig

from framework.translation import _


class DynamicSettingsConfig(AppConfig):
    name = 'dynamic_settings'
    verbose_name = _('动态配置')

    def ready(self):
        from .conf import SettingOptionsManager
        SettingOptionsManager().watch_config()
