# Generated by Django 2.0.13 on 2021-02-21 17:39

from django.db import migrations, models
import framework.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('_version', models.IntegerField(default=0, verbose_name='版本')),
                ('create_datetime', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_datetime', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('log_key', models.CharField(db_index=True, max_length=30, verbose_name='关联表标识')),
                ('log_type', models.IntegerField(default=0)),
                ('key', models.CharField(blank=True, db_index=True, default='', max_length=100, verbose_name='查询标识')),
                ('name', models.CharField(default='', max_length=100, unique=True, verbose_name='查询名称')),
                ('select', models.CharField(blank=True, max_length=1000, verbose_name='查询字段')),
                ('where', models.CharField(blank=True, max_length=500)),
                ('group', models.CharField(blank=True, default='', max_length=50, verbose_name='用途分组')),
                ('order', models.CharField(blank=True, default='', max_length=20)),
                ('order_type', models.IntegerField(choices=[(1, '倒序'), (0, '正序')], default=0)),
                ('sql', models.TextField(blank=True, default='', verbose_name='SQL')),
                ('other_sql', models.TextField(blank=True, default='', verbose_name='其他SQL')),
                ('cache_validate', models.IntegerField(default=0, null=True)),
                ('remark', models.CharField(blank=True, max_length=1000, verbose_name='备注')),
                ('_field_config', models.TextField(blank=True, default='', verbose_name='查询字段定义')),
                ('template_name', models.CharField(blank=True, max_length=32, verbose_name='模版名')),
            ],
            options={
                'ordering': ('id',),
            },
            bases=(models.Model, framework.models.SqlModelMixin),
        ),
        migrations.CreateModel(
            name='QueryResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='查询名称')),
                ('remark', models.CharField(max_length=200, verbose_name='查询说明')),
            ],
            options={
                'db_table': 'query_result',
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statistic_id', models.IntegerField(verbose_name='统计ID')),
                ('server_id', models.IntegerField(verbose_name='服务ID')),
                ('channel_id', models.IntegerField(verbose_name='渠道ID')),
                ('tag', models.IntegerField(verbose_name='标签')),
                ('result', models.FloatField(verbose_name='结果值')),
                ('create_time', models.DateTimeField(verbose_name='创建时间')),
                ('result_time', models.DateTimeField(verbose_name='结果时间')),
            ],
            options={
                'db_table': 'result',
                'ordering': ('-id',),
            },
        ),
        migrations.CreateModel(
            name='Statistic',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('_version', models.IntegerField(default=0, verbose_name='版本')),
                ('create_datetime', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_datetime', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('log_type', models.IntegerField()),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='统计标识')),
                ('remove_field', models.CharField(default='', max_length=50, verbose_name='统计时间维护字段')),
                ('is_save_center', models.IntegerField(default=1, verbose_name='是否保存到中央库')),
                ('save_table_name', models.CharField(default='log_statistic_result', max_length=50, verbose_name='保存到哪个表')),
                ('where', models.CharField(max_length=50, null=True, verbose_name='')),
                ('sql', models.CharField(max_length=5000)),
                ('exec_interval', models.IntegerField(default=0)),
                ('last_exec_time', models.DateTimeField(blank=True, null=True)),
                ('is_auto_execute', models.IntegerField(default=0, verbose_name='自动执行')),
                ('auto_exec_interval', models.IntegerField(blank=True, default=0, verbose_name='自动执行间隔')),
                ('remark', models.CharField(blank=True, max_length=1000, verbose_name='备注')),
                ('result_data', models.CharField(blank=True, max_length=200)),
            ],
            options={
                'ordering': ('-last_exec_time',),
            },
            bases=(models.Model, framework.models.SqlModelMixin),
        ),
        migrations.AddField(
            model_name='queryresult',
            name='statistic',
            field=models.ManyToManyField(to='analysis.Statistic'),
        ),
    ]