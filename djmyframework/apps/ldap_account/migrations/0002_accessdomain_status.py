# Generated by Django 3.0.13 on 2021-04-01 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessdomain',
            name='status',
            field=models.IntegerField(choices=[(0, '开启'), (1, '禁用')], default=0, verbose_name='状态'),
        ),
    ]
