from django.core.management.base import BaseCommand
from member.models import Member
from member.models import MemberStat

class Command(BaseCommand):

    def handle(self, *args, **options):
        MemberStat(member_count=Member.objects.count()).save()
