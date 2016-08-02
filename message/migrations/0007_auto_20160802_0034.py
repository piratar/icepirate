# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0006_message_wasa2il_usage'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='generate_html_mail',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='interactivemessage',
            name='interactive_type',
            field=models.CharField(max_length=60, choices=[(b'registration_received', b'Registration received'), (b'registration_confirmed', b'Registration confirmed'), (b'reject_email_messages', b'Reject mail messages'), (b'email_html_template', b'Email HTML template')]),
        ),
    ]
