from __future__ import absolute_import

import os
import shutil

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = '初始化框架 复制框架配置文件 config'

    def handle(self, **options):

        from ...settings import PROJECT_ROOT, BASE_DIR
        dir_name = 'config'
        config_dir = os.path.join(PROJECT_ROOT, dir_name)
        project_dir = BASE_DIR
        project_conf_dir = os.path.join(project_dir, dir_name)

        requirements_file = os.path.join(BASE_DIR, 'requirements.txt')
        if not os.path.isfile(requirements_file):
            open(requirements_file).write('')
        if not os.path.isdir(project_conf_dir):
            shutil.copytree(config_dir, project_conf_dir)
            print('add config %s' % project_conf_dir)
        else:
            raise Exception('%s 已经存在' % project_conf_dir)
