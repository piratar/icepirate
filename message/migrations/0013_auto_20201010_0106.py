# Generated by Django 2.2.13 on 2020-10-10 01:06

from django.db import migrations


def delete_inactive_interactive_messages(apps, schema_editor):
    InteractiveMessage = apps.get_model('message', 'InteractiveMessage')
    InteractiveMessage.objects.filter(active=False).delete()


def fake_reverse(apps, schema_editor):
    # Retrieving deleted data is impossible.
    # Function just here to make migration reversible.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0012_auto_20201009_2140'),
    ]

    operations = [
        migrations.RunPython(delete_inactive_interactive_messages, fake_reverse),
    ]
