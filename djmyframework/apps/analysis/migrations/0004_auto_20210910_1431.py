# Generated by Django 3.0.13 on 2021-09-10 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0003_auto_20210910_1423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queryserver',
            name='log_db_config',
        ),
        migrations.AlterField(
            model_name='queryserver',
            name='charset',
            field=models.CharField(default='utf8', help_text='默认 utf8', max_length=100, verbose_name='数据字符集'),
        ),
        migrations.AlterField(
            model_name='queryserver',
            name='name',
            field=models.CharField(db_index=True, help_text='纯字母', max_length=20, verbose_name='服务器名'),
        ),
        migrations.AlterField(
            model_name='queryserver',
            name='remark',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='备注'),
        ),
        migrations.AlterField(
            model_name='queryserver',
            name='user',
            field=models.CharField(default='root', max_length=100, verbose_name='用户'),
        ),
    ]
