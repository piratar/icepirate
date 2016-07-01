# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locationcode', '0001_initial'),
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='auto_locations',
            field=models.ManyToManyField(related_name='auto_location_groups', to='locationcode.LocationCode'),
        ),
        migrations.AddField(
            model_name='group',
            name='auto_subgroups',
            field=models.ManyToManyField(related_name='auto_parent_groups', to='group.Group'),
        ),
    ]
