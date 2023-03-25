# Generated by Django 3.1.10 on 2023-03-07 17:55

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myadmin', '0008_auto_20210914_1302'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='operatelog',
            options={'ordering': ['-id']},
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(db_index=True, max_length=50, unique=True, validators=[django.core.validators.RegexValidator('[\\d\\w_]+$', '字母组合,符合^[a-z][\\d\\w_]+$')], verbose_name='用户名'),
        ),
    ]