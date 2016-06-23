# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0002_member_legal_municipality_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocationCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location_code', models.CharField(unique=True, max_length=20)),
                ('location_name', models.CharField(max_length=200)),
            ],
        ),
    ]
