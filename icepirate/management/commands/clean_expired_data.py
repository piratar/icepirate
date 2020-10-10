from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from member.models import Subscriber
from message.models import ShortURL


class Command(BaseCommand):

    def handle(self, *args, **options):

        # Figure out expiry date.
        expiry_date = timezone.now() - timedelta(days=settings.EXPIRY_DAYS)

        # Delete expired stuff.
        ShortURL.objects.filter(added__lt=expiry_date).delete()
        Subscriber.objects.filter(
            temporary_web_id_timing__lt=expiry_date,
            email_verified=False
        ).delete()
