import time
import traceback
from sys import stdout, stderr

from core.loggers import log_mail

from django.core.management.base import BaseCommand
from django.utils import timezone

from icepirate.utils import quick_mail

from message.models import Message
from message.models import MessageDelivery


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("--- Script started at %s ---" % timezone.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        )

        messages = Message.objects.filter(
            ready_to_send=True,
            sending_complete=None
        )

        message_count = len(messages)
        print("Messages to process: %d" % message_count)

        for i, message in enumerate(messages):
            print('Processing message %d/%d (ID %d)' % (i+1, message_count, message.id))

            for num, recipient_count, recipient, success in message.send_bulk():
                print('  %d/%d: %s sending to %s' % (
                    num,
                    recipient_count,
                    'Success' if success else 'Failed',
                    recipient
                ))

            print('Message %d/%d (ID %d) processed.' % (i+1, message_count, message.id))

        print('--- Script complete. ---')
