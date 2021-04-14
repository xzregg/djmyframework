from django.apps import AppConfig, apps


class FrameWrokConfig(AppConfig):
    name = 'framework'


    def ready(self):
        from .conf import settings_manager
        settings_manager.watch_config()


def get_app_path(app_name):
    return apps.app_configs.get(app_name).path
