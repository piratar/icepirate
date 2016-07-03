# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locationcode', '0001_initial'),
        ('message', '0003_auto_20160701_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='locations',
            field=models.ManyToManyField(to='locationcode.LocationCode', blank=True),
        ),
    ]
