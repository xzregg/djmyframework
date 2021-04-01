from django.apps import AppConfig
from framework.translation import _

class LdapAccountConfig(AppConfig):
    name = 'ldap_account'
    label = _('Ldap 访问')
