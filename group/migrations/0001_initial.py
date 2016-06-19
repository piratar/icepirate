# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('techname', models.CharField(unique=True, max_length=50)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('added', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
