# -*- coding: utf-8 -*-

import os
import typing

from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from framework.models import BaseNameModel, models
from framework.translation import _
from framework.utils import mkdirs
from framework.utils.cache import CacheAttribute
from framework.utils.myenum import Enum
from myadmin.models import Resource, Role, User, UserInfo
from .ldap_server import get_db_path

DBPATH = get_db_path()

OU_PEOPLE_DIR = os.path.join(DBPATH, 'dc=com.dir', 'dc=example.dir', 'ou=people.dir')
OU_ROLE_DIR = os.path.join(DBPATH, 'dc=com.dir', 'dc=example.dir', 'ou=role.dir')
mkdirs(OU_PEOPLE_DIR)
mkdirs(OU_ROLE_DIR)

# mail 字段是 mindoc 需要
cn_tpl = '''dn: cn={cn},ou=people,dc=example,dc=com
objectClass: posixAccount
uid: {uid}
cn: {cn}
sn: {sn}
alias: {alias}
uidNumber: {uidNumber}
status: {status}
email: {email}
mail: {email}
employeeId: {employee_id}
userPassword: {userPassword}


'''

ou_role_tpl = '''dn: cn={cn},ou=role,dc=example,dc=com
cn: {cn}
gidNumber: {gidnumber}
parent: {parent}
alias: {alias}
description: {desc}
objectclass: posixGroup
objectclass: top
{memberuid}


'''

dc_tpl = '''dn: dc=example,dc=com
objectClass: dcObject
dc: example'''


# sourceStrin=1234546
# passlib.hash.ldap_salted_sha1.encrypt('123456')
# '{SSHA}TgL7DCvwD6UkA4mgcOkEUJf2RdSZ0xqj'


class AccessDomain(BaseNameModel):
    """访问域"""

    class Status(Enum):
        Enable = 0, _('开启')
        Disable = 1, _('禁用')

    bindpw = models.CharField(verbose_name=_('访问密钥'), max_length=30, default='', null=False)
    access_address = models.CharField(verbose_name=_('访问地址'), max_length=256, default='', null=False)
    status = models.IntegerField(verbose_name=_('状态'), choices=Status.member_list(), default=Status.Enable)

    @property
    def is_enable(self):
        return self.status == self.Status.Enable

    @property
    def basedn(self):
        return 'dc=%s,dc=com' % self.name

    def save(self, *args, **kwargs):
        self.create_ldap_access_people()
        if self.status == self.Status.Disable:
            self.delete_ldap_access_people()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.delete_ldap_access_people()
        super().delete(*args, **kwargs)

    def get_ldap_access_people(self):
        ldap_access_people = User()
        ldap_access_people.username = self.name
        ldap_access_people.alias = self.alias
        ldap_access_people.set_password(self.bindpw)
        return ldap_access_people

    def create_ldap_access_people(self):
        self.create_people(self.get_ldap_access_people())

    def delete_ldap_access_people(self):
        self.delete_people(self.get_ldap_access_people())

    def get_domain_db_path(self):
        return os.path.join(DBPATH, 'dc=com.dir', 'dc=%s.dir' % self.name)

    def create_db_dir(self, *dir_name):
        db_dir = os.path.join(self.get_domain_db_path(), *dir_name)
        mkdirs(db_dir)
        return db_dir

    @CacheAttribute
    def people_db_path(self):
        return self.create_db_dir('ou=people.dir')

    @CacheAttribute
    def role_db_path(self):
        return self.create_db_dir('ou=role.dir')

    def create_people(self, user: User):
        file_name = 'cn=%s.ldif' % user.username
        user_info = user.user_info
        employee_id = email = ''
        if user_info:
            employee_id = user_info.employee_id
            email = user_info.email
        save_path = os.path.join(self.people_db_path, file_name)
        password_tuple = user.password.split('$', 1)
        secret = '{SSHA}%s' % (password_tuple[1] if len(password_tuple) > 1 else '')

        with open(save_path, 'w') as f:
            ldap_cn_str = cn_tpl.format(cn=user.username, sn=user.alias[0], uid=user.username, alias=user.alias,
                                        uidNumber=user.id,
                                        userPassword=secret, email=email, employee_id=employee_id, status=user.status)
            f.write(ldap_cn_str)

    def delete_people(self, user):
        file_name = 'cn=%s.ldif' % user.username
        save_path = os.path.join(self.people_db_path, file_name)
        if os.path.exists(save_path):
            os.remove(save_path)

    def create_role(self, role: Role):
        file_name = 'cn=%s.ldif' % role.name
        if role.type == Role.RoleType.GROUP:
            parent = ''
            # todo 改为域限制
            if role.parent:
                parent = role.parent.name
            ou_role_dir = self.role_db_path
            save_path = os.path.join(ou_role_dir, file_name)
            memberuid_list = '\n'.join(['memberUid: %s' % v for v in role.user_set.all().values_list('username')])

            with open(save_path, 'w') as f:
                ldap_cn_str = ou_role_tpl.format(cn=role.name, parent=parent, gidnumber=role.id, alias=role.alias,
                                                 desc=role.remark, memberuid=memberuid_list)
                f.write(ldap_cn_str)

    def delete_role(self, role: Role):
        file_name = 'cn=%s.ldif' % role.name
        save_path = os.path.join(self.role_db_path, file_name)
        if os.path.exists(save_path):
            os.remove(save_path)

    class Meta:
        pass


@receiver(post_save, sender=User, dispatch_uid="user_save_ldap")
def user_save_ldap(sender, instance: User, update_fields=None, **kwargs):
    user: User = instance

    access_domain_list: typing.List[AccessDomain] = user.get_resource('access_domain')

    for access_domain in access_domain_list:
        if access_domain.is_enable and user.status == User.Status.NORMAL and update_fields is None:
            access_domain.create_people(user)
        else:
            access_domain.delete_people(user)


@receiver(pre_delete, sender=User, dispatch_uid="user_delete_ldap")
def user_delete_ldap(sender, instance: User, **kwargs):
    for access_domain in instance.get_resource('access_domain'):
        access_domain.delete_people(instance)


# @receiver(post_save, sender=Role, dispatch_uid="role_save_ldap")
def role_save_ldap(sender, instance: Role, **kwargs):
    role = instance
    access_domain_list = role.get_resource('access_domain').values_list('id',flat=True)
    all_access_domain_list: typing.List[AccessDomain] = AccessDomain.objects.all()

    for access_domain in all_access_domain_list:
        if role.type == Role.RoleType.GROUP and access_domain.id in access_domain_list:
            access_domain.create_role(role)
        else:
            access_domain.delete_role(role)


@receiver(pre_delete, sender=Role, dispatch_uid="role_delete_ldap")
def role_delete_ldap(sender, instance: Role, **kwargs):
    role = instance
    access_domain_list: typing.List[AccessDomain] = AccessDomain.objects.all()
    for access_domain in access_domain_list:
        access_domain.delete_role(role)


@receiver(post_save, sender=UserInfo, dispatch_uid="user_info_save_ldap")
def user_info_save_ldap(sender, instance: UserInfo, **kwargs):
    user = instance.user
    user_save_ldap(sender, user)


@receiver(pre_delete, sender=UserInfo, dispatch_uid="user_info_delete_ldap")
def user_info_delete_ldap(sender, instance: UserInfo, **kwargs):
    user = instance.user
    user_delete_ldap(sender, user)


@receiver(post_save, sender=Resource, dispatch_uid="role_access_domain_resource_save")
def role_access_domain_resource_save(sender, instance: Resource, **kwargs):
    if instance.name == 'access_domain':
        role = instance.role_set.first()
        if role:
            role_save_ldap(sender, role)

# todo 按照模型同步 db 文件逻辑负载,尝试实现 ldap server 协议
#@receiver(m2m_changed, sender=User.role.through, dispatch_uid="user_add_role_ldap")
def user_add_role_ldap(sender, action, instance: Role, reverse, model: Role, pk_set, using, **kwargs):
    if action in['post_add','post_clear','post_remove']:
        user_save_ldap(sender, instance)
    # role_save_ldap(sender,model)
    # print('user_role_add_ldap')
    # print(sender,kwargs)
