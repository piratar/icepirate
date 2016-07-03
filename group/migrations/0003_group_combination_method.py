# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0002_auto_20160701_1636'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='combination_method',
            field=models.CharField(default=b'union', max_length=30, verbose_name=b'Combination method', choices=[(b'union', b'Union'), (b'intersection', b'Intersection')]),
        ),
    ]
