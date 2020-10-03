import time
import traceback
from sys import stdout, stderr

from django.core.management.base import BaseCommand
from django.utils import timezone

from icepirate.utils import quick_mail

from message.models import Message
from message.models import MessageDelivery


class Command(BaseCommand):

    def handle(self, *args, **options):
        stdout.write("Processing started at %s\n" % timezone.now())

        messages = Message.objects.filter(
            ready_to_send=True, sending_started=None, sending_complete=None)
        stdout.write("Messages to process: %d\n" % len(messages))

        # Do this first, to reduce the odds of races where messages get
        # sent more than once.
        for message in messages:
            message.sending_started = timezone.now()
            message.save()

        # Try to process all the messages.
        for message in messages:
            try:
                self._process_message(message)
            except:
                pass  # Still try to process the rest!

    def _get_message_recipients(self, message):
        stdout.write("- Generating recipient list...")
        recipients = message.get_undelivered_recipients()
        stdout.write(" done. (%d)\n" % len(recipients))
        return recipients

    def _process_message(self, message):
        stdout.write(
           "Starting processing of message with ID %d\n" % message.id)

        recipients = self._get_message_recipients(message)
        recipient_count = len(recipients)

        for i, recipient in enumerate(recipients):
            try:
                stdout.write(
                    "- (%d/%d) Mailing message with ID %d to %s..." % (
                        i+1, recipient_count, message.id, recipient.email))

                # Note: This may have the side effect of setting the
                #       recipient's temporary_web_id attribute.
                body = message.get_bodies(recipient)
                stdout.write('.')

                delivery = MessageDelivery()
                delivery.member = recipient
                delivery.message = message
                delivery.save()
                stdout.write('.')

                quick_mail(
                    to=recipient.email,
                    subject=message.subject,
                    body=body,
                    from_email=message.from_address,
                    subject_prefix=None)
                stdout.write('.')

                delivery.timing_end = timezone.now()
                delivery.save()

                stdout.write(" done.\n")
            except:
                stdout.write(" FAILED!\n")
                traceback.print_exc(file=stderr)

        message.sending_complete = timezone.now()
        message.save()

