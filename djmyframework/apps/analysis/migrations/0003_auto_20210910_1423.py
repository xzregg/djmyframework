# Generated by Django 3.0.13 on 2021-09-10 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0002_auto_20210910_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queryserver',
            name='alias',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='服务器别名'),
        ),
        migrations.AlterField(
            model_name='queryserver',
            name='name',
            field=models.CharField(db_index=True, max_length=20, verbose_name='服务器名称'),
        ),
    ]
