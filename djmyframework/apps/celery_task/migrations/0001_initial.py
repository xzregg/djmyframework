# Generated by Django 2.0.13 on 2021-02-21 17:39

from django.db import migrations, models
import framework.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('django_celery_results', '0004_auto_20190516_0412'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssociatedTaskResult',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('_version', models.IntegerField(default=0, verbose_name='版本')),
                ('create_datetime', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_datetime', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('a_id', models.BigIntegerField(db_index=True, verbose_name='关联作业标识')),
                ('a_type_name', models.CharField(db_index=True, max_length=50, verbose_name='关联作业类型')),
                ('task_result', models.ManyToManyField(to='django_celery_results.TaskResult', verbose_name='celert 任务结果集')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
            bases=(models.Model, framework.models.SqlModelMixin),
        ),
    ]
