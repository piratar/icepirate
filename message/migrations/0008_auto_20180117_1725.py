# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0007_auto_20160802_0034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interactivemessage',
            name='subject',
            field=models.CharField(default=b'[SomeApp] ', max_length=300),
        ),
        migrations.AlterField(
            model_name='message',
            name='subject',
            field=models.CharField(default=b'[SomeApp] ', max_length=300),
        ),
    ]
