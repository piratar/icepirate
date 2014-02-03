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

