#!/usr/bin/env python

import os
import shutil

djframework_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_djframework():
    target_project_dir = os.getcwd()
    dir_name = 'config'
    config_dir = os.path.join(djframework_dir, dir_name)
    project_dir = target_project_dir
    project_conf_dir = os.path.join(project_dir, dir_name)

    requirements_file = os.path.join(target_project_dir, 'requirements.txt')
    if not os.path.isfile(requirements_file):
        open(requirements_file).write('')
    if not os.path.isdir(project_conf_dir):
        shutil.copytree(config_dir, project_conf_dir)
        print('add config %s' % project_conf_dir)
    else:
        raise Exception('%s 已经存在' % project_conf_dir)


if __name__ == '__main__':
    os.system('yum install openldap-devel')
    os.system('pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --ignore-installed')
