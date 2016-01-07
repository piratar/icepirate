from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from group.models import Group
from member.models import Member

class Message(models.Model):

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField()

    send_to_all = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)

    recipient_list = models.ManyToManyField(Member, related_name='recipient_list') # Constructed at time of processing
    deliveries = models.ManyToManyField(Member, related_name='deliveries', through='MessageDelivery') # Members already sent to
    author = models.ForeignKey(User) # User, not Member

    ready_to_send = models.BooleanField(default=False) # Should this message be processed?

    sending_started = models.DateTimeField(null=True) # Marked when processing beings
    sending_complete = models.DateTimeField(null=True) # Marked when processing ends

    added = models.DateTimeField(default=timezone.now) # Automatic, un-editable field

    class Meta:
        ordering = ['added']

class MessageDelivery(models.Model):
    message = models.ForeignKey(Message)
    member = models.ForeignKey(Member)
    timing_start = models.DateTimeField(default=timezone.now)
    timing_end = models.DateTimeField(null=True)

class InteractiveMessage(models.Model):

    INTERACTIVE_TYPES = (
        ('registration_received', 'Registration received'),
        ('registration_confirmed', 'Registration confirmed'),
        ('reject_email_messages', 'Reject mail messages'),
    )

    INTERACTIVE_TYPES_DETAILS = {
        'registration_received': {
            'description': 'Use the strings {{confirm}} and {{reject}}\nto place confirmation and rejection links.',
            'links': ('confirm', 'reject'),
        },
        'reject_email_messages': {
            'description': 'Use the string {{reject_link}} to place\nthe rejection link.',
            'links': ('reject_link',),
        },
    }

    interactive_type = models.CharField(max_length=60, choices=INTERACTIVE_TYPES)
    active = models.BooleanField(default=True)

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField()

    deliveries = models.ManyToManyField(Member, related_name='interactive_deliveries', through='InteractiveMessageDelivery')
    author = models.ForeignKey(User) # User, not member

    added = models.DateTimeField(default=timezone.now) # Automatic, un-editable field

    def produce_links(self, random_string):
        result = self.body

        for link_name in InteractiveMessage.INTERACTIVE_TYPES_DETAILS[self.interactive_type]['links']:
            link = '%s/message/mailcommand/%s/%s/%s/' % (settings.SITE_URL, self.interactive_type, link_name, random_string)
            result = result.replace('{{%s}}' % link_name, link)

        return result

    class Meta:
        ordering = ['interactive_type', 'added']

class InteractiveMessageDelivery(models.Model):
    interactive_message = models.ForeignKey('InteractiveMessage')
    member = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL)
    email = models.CharField(max_length=75)
    timing_start = models.DateTimeField(default=timezone.now)
    timing_end = models.DateTimeField(null=True)

