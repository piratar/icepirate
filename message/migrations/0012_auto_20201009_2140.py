# Generated by Django 2.2.13 on 2020-10-09 21:40

from django.db import migrations
from django.db.models import Count
from django.db.models import F
from django.db.models import Q


def update_message_data(apps, schema_editor):
    Member = apps.get_model('member', 'Member')
    Message = apps.get_model('message', 'Message')
    MessageDelivery = apps.get_model('message', 'MessageDelivery')

    # This is a function needed by `get_recipients` below.
    def get_members(self, subgroups=True):

        membergroup_ids = set([self.id])
        if subgroups:
            membergroup_ids |= set(self.auto_subgroups.values_list('id', flat=True))
        mQs = Q(membergroups__id__in = membergroup_ids)

        return Member.objects.filter(mQs).distinct()

    # This is the old `get_recipients` function, which has been completely
    # rewritten as a part of the `Message` model. Previously, it was used to
    # calculate how many recipients there were to messages that had been
    # delivered in the past, meaning that the stated number in the message
    # administration became unrealiable as time passed. When a member is
    # removed from the registry altogether, for example, the count goes down,
    # even though the message wasn't sent to any fewer people in the past.
    # This mechanism has been replaced with an almost entirely new one, that
    # records how many recipients there are at the time of the message being
    # sent. We still want to retain what information we still have, even if
    # imprecise. The interface will have to denote this information as
    # dubious, but it will still give some hint of how many messages were sent
    # at the time of sending.
    def get_recipients(message):
        def rcpt_filter(q):
            if message.sending_started:
                q = q.filter(added__lt=message.sending_started)
            return q.filter(Q(email_wanted=True) | Q(email_wanted=None, email_unwanted=False))

        recipients = []
        if message.send_to_all:
            recipients = rcpt_filter(Member.objects)
        else:
            for membergroup in message.membergroups.all():
                recipients.extend(rcpt_filter(get_members(
                    membergroup,
                    subgroups=message.groups_include_subgroups
                )))

        return list(set(recipients))

    # 1. Update delivery counts of messages.
    messages = Message.objects.annotate(delivery_count=Count('deliveries'))
    for message in messages:
        # We will mark the recipient count as a negative number to indicate
        # that it is actually wrong. In reality, it is kind-of correct-ish
        # (see comment for `get_recipients` above), but without that
        # knowledge, it is better to give the impression that it's completely
        # wrong than it being accurate. The web interface will interpret this
        # for the user with an appropriate expanation, precisely by detecting
        # whether it's a negative number or not.
        message.recipient_count = 0 - len(get_recipients(message))
        message.save()
        print('.', end='', flush=True)

    # 2. Mark all existing bulk sends as complete.
    # This is needed because before, messages were not processed if processing
    # had started, meaning that processing of failed bulks was not attempted
    # again, but dealt with manually (by writing and sending a new message,
    # presumably). Now, however, attempts are made to process messages again
    # if they have not completed, resuming from wherever a previous attempt
    # stopped. This means that if there are earlier messages in the database
    # now, that have failed for some reason eons ago, we do **not** want them
    # all to be resumed now, because the previous failures have already been
    # dealt. At least, receiving some ancient messages now isn't going to fix
    # anything. Therefore, we deem all existing messages as completed, and
    # incorrectly (and implausibly) set the completion time as the same as the
    # starting time, just to have some value in the completion field.
    Message.objects.exclude(
        sending_started=None
    ).filter(
        sending_complete=None
    ).update(
        sending_complete=F('sending_started')
    )

    # 3. Delete old DeliveryMessage data.
    # Specifically, all of it. It will only live during the sending of
    # messages, from now on.
    MessageDelivery.objects.all().delete()


def fake_reverse(apps, schema_editor):
    # This function is only here for the migration to be reversable.
    # When message data is updated, the data needed to create the data
    # backwards is deleted. This is fine, we still want reversability.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0011_auto_20201009_2032'),
    ]

    operations = [
        migrations.RunPython(update_message_data, fake_reverse)
    ]