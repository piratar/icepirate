import sys

from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from member.models import MemberGroup
from member.models import Member

from icepirate.utils import quick_mail

class Command(BaseCommand):

    def handle(self, *args, **options):

        membergroups = MemberGroup.objects.all()
        for membergroup in membergroups:
            subject = 'Statistics for membergroup "%s"' % membergroup.name
            body = []

            body.append('These are the member statistics for the membergroup "%s"' % membergroup.name)
            body.append('Member count: %d' % membergroup.members.count())

            sys.stdout.write('Sending member statistics for membergroup \'%s\'...' % membergroup.techname)
            quick_mail(membergroup.email, subject, '\n'.join(body))
            sys.stdout.write(' done\n')


