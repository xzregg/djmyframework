# Generated by Django 3.0.13 on 2021-09-10 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_auto_20210910_1431'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='is_paging',
            field=models.BooleanField(default=False, verbose_name='是否分页'),
        ),
    ]