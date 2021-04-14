# -*- coding: utf-8 -*-
# @Time    : 2021-04-14 18:00
# @Author  : xzr
# @File    : conf
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

import json

import etcd3
from django.conf import empty, LazySettings, settings as _settings
from django.utils.encoding import force_str
from etcd3.watch import WatchResponse

from framework.utils.signals import add_signal_handler, signal


class AbsSettingsBackend(object):

    def get_value(self, name): pass

    def set_value(self, name, value): pass

    def watch_config(self): pass


class Etcd3SettingsBackend(AbsSettingsBackend):
    prefix_key = '/django/settings/'
    config = {}

    def __init__(self):
        _SETINGS_ETCD = getattr(_settings, 'SETINGS_ETCD', {})
        prefix_key = _SETINGS_ETCD.pop('prefix_key', 'default')
        self.prefix_key = '%s%s/' % (self.prefix_key, prefix_key)
        self.etcd = etcd3.client(**_SETINGS_ETCD)
        self.init_config()
        self.watch_id = None

    def watch_config(self):
        self.watch_id = self.etcd.add_watch_prefix_callback(self.prefix_key, self.watch_callback)

        add_signal_handler(signal.SIGTERM, self.cancel)
        add_signal_handler(signal.SIGINT, self.cancel)

    def cancel(self):
        if self.watch_id:
            self.etcd.cancel_watch(self.watch_id)

    def init_config(self):
        for value, metadata in self.etcd.get_prefix(self.prefix_key):
            config_name = self.get_config_name_from_event_key(metadata.key)
            self.config[config_name] = json.loads(value)

    def genrate_key(self, name):
        return '%s%s' % (self.prefix_key, name.strip())

    def set_value(self, name, value):
        self.etcd.put(self.genrate_key(name), json.dumps(value))

    def get_value(self, name, default_value=None):
        value = self.config.get(name, None)
        if value is None:
            value, metadata = self.etcd.get(self.genrate_key(name))
            if metadata:
                value = json.loads(value)
            else:
                value = default_value
                self.set_value(name, value)
                self.config[name] = value
        return value

    def watch_callback(self, rsp: etcd3.watch.WatchResponse):
        for event in rsp.events:
            config_name = self.get_config_name_from_event_key(event.key)
            self.config[config_name] = json.loads(event.value)

    def get_config_name_from_event_key(self, key):
        name = force_str(key)[len(self.prefix_key):]
        return name


class Settings(LazySettings):
    def __getattr__(self, name):
        """Return the value of a setting and cache it in self.__dict__."""
        if self._wrapped is empty:
            self._setup(name)
        val = getattr(self._wrapped, name)
        if isinstance(val, SettingOptions):
            val.set_name(name)
            val = val.get_value()
        self.__dict__[name] = val
        return val

    def merge(self, settings_dict):
        pass


settings = Settings()


def get_settings_backend():
    return Etcd3SettingsBackend()


class SettingOptionsManager(object):
    settings_options_map = {}
    backend: AbsSettingsBackend = get_settings_backend()

    def genrate_options_key(self, options):
        return '%s/%s' % (options.group, options.name)

    def get_value(self, name):
        options: SettingOptions = self.settings_options_map.get(name, None)
        if options:
            name = self.genrate_options_key(options)
            value = self.backend.get_value(name, options.default_value)
            return value if value is not None else options.default_value

    def set_value(self, name, value):
        options: SettingOptions = self.settings_options_map.get(name, None)
        if options:
            name = self.genrate_options_key(options)
            return self.backend.set_value(name, value)

    def watch_config(self):
        self.backend.watch_config()


settings_manager = SettingOptionsManager()


class SettingOptions(object):
    manager = settings_manager

    def __init__(self, default_value, alias, name=None, group='defaults', choices=None, type=str):
        self.alias = alias
        self.type = type
        self.default_value = default_value
        self.choices = choices
        self.name = name
        self.group = group
        self._join_to_manager()

    def _join_to_manager(self):
        if self.name is not None:
            self.manager.settings_options_map[self.name] = self

    def set_name(self, name):
        if self.name is None:
            self.name = force_str(name).strip()
            self._join_to_manager()

    def get_value(self):
        if self.name:
            return self.type(self.manager.get_value(self.name))

    def set_value(self, value):
        return self.manager.set_value(self.name, value)

    def __get__(self, instance, owner):
        return self.get_value()

    def __str__(self):
        return self.get_value()


class __SettingOptions(object):

    def __new__(cls, *args, **kwargs) -> _SettingOptions:
        value = args[0]
        python_class_type = type(value)

        _clazz = type(
                cls.__name__,
                (_SettingOptions,python_class_type(value)),
                {}
        )

        return _clazz(*args, **kwargs)
