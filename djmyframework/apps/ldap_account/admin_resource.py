# -*- coding: utf-8 -*-
# @Time    : 2020-09-15 14:35
# @Author  : xzr
# @File    : user_resource
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from framework.translation import _
from myadmin.models.resource import ModelResource, Resource
from . import models


class AccessDomainModelResource(ModelResource):
    label = _('访问域')
    name = 'access_domain'
    model_class = models.AccessDomain
    template = ModelResource.default_template


Resource.register(AccessDomainModelResource())
