# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import quopri


def fix_names(apps, schema_editor):
    Member = apps.get_model('member', 'Member')

    members = Member.objects.filter(name__endswith='T=C3=B6lvup=C3=B3stfang')
    for member in members:
        member.name = member.name[:-26] # Remove 'Tölvupóstfang'
        member.name = quopri.decodestring(member.name).decode('utf-8') # Decode Quotable-Print.
        member.save()


# Only here to allow reversing migrations.
def dummy_function(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0004_delete_locationcode'),
    ]

    operations = [
        migrations.RunPython(fix_names, dummy_function),
    ]
