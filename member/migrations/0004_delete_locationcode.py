# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0004_message_locations'),
        ('member', '0003_locationcode'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LocationCode',
        ),
    ]
