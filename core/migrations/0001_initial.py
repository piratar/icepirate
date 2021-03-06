# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-15 16:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('member', '0002_membergroup_admins'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timing', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(choices=[('member_add', 'Member added'), ('member_edit', 'Member edited'), ('member_delete', 'Member deleted'), ('member_view', 'Member viewed'), ('member_search', 'Member search')], max_length=50)),
                ('action_details', models.CharField(max_length=500, null=True)),
                ('affected_member_count', models.IntegerField(default=0)),
                ('affected_members', models.ManyToManyField(to='member.Member')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timing'],
            },
        ),
    ]
