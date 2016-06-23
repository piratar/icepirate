from sys import stdout, stderr

from django.core.management.base import BaseCommand
from django.utils import timezone

from icepirate.utils import generate_random_string
from icepirate.utils import quick_mail

from group.models import Group
from member.models import Member
from message.models import InteractiveMessage
from message.models import Message
from message.models import MessageDelivery

class Command(BaseCommand):

    def handle(self, *args, **options):

        stdout.write("Processing started at %s\n" % timezone.now())

        messages = Message.objects.filter(ready_to_send=True, sending_started=None, sending_complete=None)

        stdout.write("Messages to process: %d\n" % len(messages))

        for message in messages:
            stdout.write("Starting processing of message with ID %d\n" % message.id)

            message.sending_started = timezone.now()
            message.save()

            stdout.write("- Generating recipient list...")

            recipients = []
            if message.send_to_all:
                recipients = Member.objects.filter(email_unwanted=False)
            else:
                for group in message.groups.all():
                    recipients.extend(group.members.filter(email_unwanted=False))

                for location in message.locations.all():
                    recipients.extend(location.get_members())

            # NOTE: If a MessageDelivery exists for a user but timing_end=None, then previous sending must have failed
            already_delivered = [d.member for d in message.messagedelivery_set.select_related('member').exclude(timing_end=None)]
            # Remove duplicates (member may be in several groups) and those already delivered to
            recipients = list(set(recipients) - set(already_delivered))

            # Get recipient count since we'll be printing it to screen a lot
            recipient_count = len(recipients)

            stdout.write(" done. (%d)\n" % recipient_count)

            i = 0
            for recipient in recipients:
                i = i + 1

                stdout.write("- (%d/%d) Mailing message with ID %d to %s..." % (i, recipient_count, message.id, recipient.email))

                body = message.body

                try:
                    rejection_message = InteractiveMessage.objects.get(interactive_type='reject_email_messages')
                    if not recipient.temporary_web_id:
                        random_string = generate_random_string()
                        while Member.objects.filter(temporary_web_id=random_string).count() > 0:
                            # Preventing duplication errors
                            random_string = generate_random_string()

                        recipient.temporary_web_id = random_string
                        recipient.save()

                    rejection_body = rejection_message.produce_links(recipient.temporary_web_id)
                    body += '\n\n------------------------------\n'
                    body += rejection_body
                except InteractiveMessage.DoesNotExist:
                    pass

                delivery = MessageDelivery()
                delivery.member = recipient
                delivery.message = message
                delivery.save()

                quick_mail(
                    to=recipient.email,
                    subject=message.subject,
                    body=body,
                    from_email=message.from_address,
                    subject_prefix=None
                )

                delivery.timing_end = timezone.now()
                delivery.save()

                stdout.write(" done.\n")

            if i == recipient_count: # Something went wrong if this is false
                message.sending_complete = timezone.now()
                message.save()

