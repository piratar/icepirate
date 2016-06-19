# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='legal_municipality_code',
            field=models.CharField(max_length=5, null=True),
        ),
    ]
