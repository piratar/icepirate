# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('group', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InteractiveMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interactive_type', models.CharField(max_length=60, choices=[(b'registration_received', b'Registration received'), (b'registration_confirmed', b'Registration confirmed'), (b'reject_email_messages', b'Reject mail messages')])),
                ('active', models.BooleanField(default=True)),
                ('from_address', models.EmailField(default=b'username@example.com', max_length=254)),
                ('subject', models.CharField(default=b'[[unspecified]] ', max_length=300)),
                ('body', models.TextField()),
                ('added', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['interactive_type', 'added'],
            },
        ),
        migrations.CreateModel(
            name='InteractiveMessageDelivery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=75)),
                ('timing_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('timing_end', models.DateTimeField(null=True)),
                ('interactive_message', models.ForeignKey(to='message.InteractiveMessage')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='member.Member', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_address', models.EmailField(default=b'username@example.com', max_length=254)),
                ('subject', models.CharField(default=b'[[unspecified]] ', max_length=300)),
                ('body', models.TextField()),
                ('send_to_all', models.BooleanField(default=True)),
                ('ready_to_send', models.BooleanField(default=False)),
                ('sending_started', models.DateTimeField(null=True)),
                ('sending_complete', models.DateTimeField(null=True)),
                ('added', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['added'],
            },
        ),
        migrations.CreateModel(
            name='MessageDelivery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timing_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('timing_end', models.DateTimeField(null=True)),
                ('member', models.ForeignKey(to='member.Member')),
                ('message', models.ForeignKey(to='message.Message')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='deliveries',
            field=models.ManyToManyField(related_name='deliveries', through='message.MessageDelivery', to='member.Member'),
        ),
        migrations.AddField(
            model_name='message',
            name='groups',
            field=models.ManyToManyField(to='group.Group'),
        ),
        migrations.AddField(
            model_name='message',
            name='recipient_list',
            field=models.ManyToManyField(related_name='recipient_list', to='member.Member'),
        ),
        migrations.AddField(
            model_name='interactivemessage',
            name='deliveries',
            field=models.ManyToManyField(related_name='interactive_deliveries', through='message.InteractiveMessageDelivery', to='member.Member'),
        ),
    ]
