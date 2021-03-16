#!/usr/bin/env python
# coding=utf-8
# 启动后台服务器的守护进程


import os
import sys
from config.daemon_service import DAEMON_SERVICE_MAP

def main():
    pwd = os.getcwd()
    supervisor_configfile = os.path.join(pwd, 'configfile', 'supervisord.ini')
    if not os.path.isfile(supervisor_configfile):
        raise Exception('%s not exists' % supervisor_configfile)
    supervisord_cmd = 'supervisord -c %s' % supervisor_configfile
    cmd = supervisorctl_cmd = 'supervisorctl -c %s' % (supervisor_configfile)

    if len(sys.argv) > 1:
        argv_str = ' '.join(sys.argv[1:])
        action = sys.argv[1]
        cmd = '%s %s' % (supervisorctl_cmd, argv_str)

    is_supervisord_running = os.system(supervisorctl_cmd + ' pid') == 0
    if not is_supervisord_running :
        print('supervisord not running,start now!\n%s' % supervisord_cmd)
        os.system(supervisord_cmd)
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    main()
