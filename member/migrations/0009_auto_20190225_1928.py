# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-25 19:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locationcode', '0001_initial'),
        ('member', '0008_auto_20180525_1647'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('techname', models.CharField(max_length=50, unique=True)),
                ('email', models.EmailField(max_length=191, unique=True)),
                ('added', models.DateTimeField(default=datetime.datetime.now)),
                ('combination_method', models.CharField(choices=[(b'union', b'Union'), (b'intersection', b'Intersection')], default=b'union', max_length=30, verbose_name=b'Combination method')),
                ('auto_locations', models.ManyToManyField(related_name='auto_location_membergroups', to='locationcode.LocationCode')),
                ('auto_subgroups', models.ManyToManyField(related_name='auto_parent_membergroups', to='member.MemberGroup')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='member',
            name='membergroups',
            field=models.ManyToManyField(related_name='members', to='member.MemberGroup'),
        ),
    ]
