from django.core.management.base import BaseCommand
from django.utils.timezone import now
from member.models import Member
from member.models import MemberStat

class Command(BaseCommand):

    def handle(self, *args, **options):
        MemberStat(timing=now(), member_count=Member.objects.count()).save()
