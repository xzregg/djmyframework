# -*- coding: utf-8 -*-
# @Time    : 2023/3/21 16:39 
# @Author  : xzr
# @File    : test_shardingmodel.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :

from framework.tests import *
from framework.models import BaseModel, ShardingModelMixin, models, MonthShardingModel
import pytest


@pytest.mark.django_db(databases='__all__')
def test_shardingmodel():
    class FooShardingModel(BaseModel, MonthShardingModel):
        f1 = models.CharField(default='')
        f2 = models.CharField(default='')
        f3 = models.IntegerField(default='')

        class Meta:
            app_label = 'framework'
            db_table = 'FooShardingModel'

    FooShardingModel.create_sharding_table()
    model_cls = FooShardingModel.get_sharding('s1')

    qs = model_cls.objects.all()

    print(qs.query)
    print(model_cls.objects.filter(f2='asd').query)
    print(model_cls._meta.db_table)
