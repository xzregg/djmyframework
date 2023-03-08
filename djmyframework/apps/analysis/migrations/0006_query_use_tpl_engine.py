# Generated by Django 3.1.10 on 2023-03-07 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0005_query_is_paging'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='use_tpl_engine',
            field=models.BooleanField(default=False, help_text='是否使用 jinjia2 模板引擎渲染sql', verbose_name='是否使用模板引擎'),
        ),
    ]
