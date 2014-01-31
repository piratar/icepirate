import sys

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from group.models import Group
from member.models import Member

from icepirate.utils import email

class Command(BaseCommand):

    def handle(self, *args, **options):

        groups = Group.objects.all()
        for group in groups:
            subject = _('Statistics for group "%s"') % group.name
            body = []

            body.append(_('These are the member statistics for the group "%s"') % group.name)
            body.append(_('Member count: %d') % group.member_set.count())

            sys.stdout.write('Sending member statistics for group \'%s\'...' % group.techname)
            email(group.email, subject, '\n'.join(body))
            sys.stdout.write(' done\n')


