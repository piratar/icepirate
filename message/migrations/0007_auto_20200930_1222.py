# Generated by Django 2.2.13 on 2020-09-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0006_auto_20200930_1210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='generate_html_mail',
        ),
        migrations.AlterField(
            model_name='interactivemessage',
            name='interactive_type',
            field=models.CharField(choices=[('registration_received', 'Registration received'), ('registration_confirmed', 'Registration confirmed'), ('reject_email_messages', 'Reject mail messages'), ('mailinglist_confirmation', 'Mailing list confirmation'), ('remind_membership', 'Reminder of existing membership')], max_length=60),
        ),
    ]
