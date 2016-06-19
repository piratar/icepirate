# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('group', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ssn', models.CharField(unique=True, max_length=30)),
                ('name', models.CharField(max_length=63)),
                ('username', models.CharField(max_length=50, unique=True, null=True, blank=True)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('email_verified', models.BooleanField(default=False)),
                ('email_unwanted', models.BooleanField(default=False)),
                ('phone', models.CharField(max_length=30, blank=True)),
                ('partake', models.BooleanField(default=False)),
                ('added', models.DateTimeField(default=datetime.datetime.now)),
                ('mailing', models.BooleanField(default=False)),
                ('verified', models.BooleanField(default=False)),
                ('auth_token', models.CharField(max_length=100, unique=True, null=True)),
                ('auth_timing', models.DateTimeField(null=True)),
                ('legal_name', models.CharField(max_length=63)),
                ('legal_address', models.CharField(max_length=63)),
                ('legal_zip_code', models.CharField(max_length=3, null=True)),
                ('legal_zone', models.CharField(max_length=63, null=True)),
                ('legal_lookup_timing', models.DateTimeField(null=True)),
                ('temporary_web_id', models.CharField(max_length=40, unique=True, null=True)),
                ('temporary_web_id_timing', models.DateTimeField(null=True)),
                ('groups', models.ManyToManyField(related_name='members', to='group.Group')),
            ],
            options={
                'ordering': ['added', 'name'],
            },
        ),
    ]
