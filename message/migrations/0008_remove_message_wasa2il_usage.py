# Generated by Django 2.2.13 on 2020-09-30 16:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0007_auto_20200930_1222'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='wasa2il_usage',
        ),
    ]
