# Generated by Django 2.2.13 on 2020-09-30 17:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0005_auto_20200930_1735'),
        ('message', '0009_auto_20200930_1735'),
        ('locationcode', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LocationCode',
        ),
    ]
