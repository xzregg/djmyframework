# Generated by Django 3.1.7 on 2021-03-25 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myadmin', '0002_auto_20210225_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
        migrations.AlterField(
            model_name='user',
            name='login_count',
            field=models.IntegerField(blank=True, default=0, verbose_name='登录次数'),
        ),
    ]
