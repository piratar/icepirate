# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-21 21:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0005_fix_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='email_wanted',
            field=models.BooleanField(default=False),
        ),
    ]
