# Generated by Django 3.0.13 on 2021-04-20 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sync_model', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='syncmodel',
            name='is_old',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]