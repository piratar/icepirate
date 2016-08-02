# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0005_shorturl'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='wasa2il_usage',
            field=models.CharField(default=b'any', max_length=12, choices=[(b'any', b'Does not matter'), (b'are_users', b'Recipients are wasa2il users'), (b'not_users', b'Recipients are not wasa2il users')]),
        ),
    ]
