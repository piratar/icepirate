# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0002_message_locations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='locations',
        ),
        migrations.AddField(
            model_name='message',
            name='groups_include_locations',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='message',
            name='groups_include_subgroups',
            field=models.BooleanField(default=True),
        ),
    ]
