from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from group.models import Group
from member.models import Member
from locationcode.models import LocationCode
from member.models import Member


class Message(models.Model):
    WASA2IL_ANY = 'any'
    WASA2IL_USERS = 'are_users'
    WASA2IL_NON_USERS = 'not_users'
    WASA2IL_MEMBERSHIP_TYPES = (
        (WASA2IL_ANY, 'Does not matter'),
        (WASA2IL_USERS, 'Recipients are wasa2il users'),
        (WASA2IL_NON_USERS, 'Recipients are not wasa2il users'))

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField()

    send_to_all = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    groups_include_subgroups = models.BooleanField(default=True)
    groups_include_locations = models.BooleanField(default=True)
    locations = models.ManyToManyField(LocationCode, blank=True)

    wasa2il_usage = models.CharField(max_length=12,
        choices=WASA2IL_MEMBERSHIP_TYPES,
        default=WASA2IL_ANY)

    recipient_list = models.ManyToManyField(Member, related_name='recipient_list') # Constructed at time of processing
    deliveries = models.ManyToManyField(Member, related_name='deliveries', through='MessageDelivery') # Members already sent to
    author = models.ForeignKey(User) # User, not Member

    ready_to_send = models.BooleanField(default=False) # Should this message be processed?

    sending_started = models.DateTimeField(null=True) # Marked when processing beings
    sending_complete = models.DateTimeField(null=True) # Marked when processing ends

    added = models.DateTimeField(default=timezone.now) # Automatic, un-editable field

    def get_recipients(message):
        def rcpt_filter(q):
            if message.sending_started:
                q = q.filter(added__lt=message.sending_started)
            if message.wasa2il_usage == message.WASA2IL_USERS:
                q = q.filter(username__isnull=False)
            elif message.wasa2il_usage == message.WASA2IL_NON_USERS:
                q = q.filter(username__isnull=True)
            return q.filter(email_unwanted=False)

        recipients = []
        if message.send_to_all:
            recipients = rcpt_filter(Member.objects)
        else:
            for group in message.groups.all():
                recipients.extend(rcpt_filter(group.get_members(
                    subgroups=message.groups_include_subgroups,
                    locations=message.groups_include_locations)))

            for location in message.locations.all():
                recipients.extend(rcpt_filter(location.get_members()))

        return list(set(recipients))

    def get_undelivered_recipients(message):
        recipients = message.get_recipients()

        # NOTE: If a MessageDelivery exists for a user but timing_end=None,
        #       then previous sending must have failed.
        already_delivered = [d.member for d in
            message.messagedelivery_set.select_related(
                'member').exclude(timing_end=None)]

        # Remove duplicates (member may be in several groups) and those
        # already delivered to.
        return list(set(recipients) - set(already_delivered))

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


class ShortURL(models.Model):
    added = models.DateTimeField(default=timezone.now)
    code = models.CharField(max_length=20, unique=True, null=True)
    url = models.CharField(max_length=1024)

    @classmethod
    def Expired(cls):
        return timezone.now() - datetime.timedelta(days=20)

    @classmethod
    def DeleteExpired(cls):
        ShortURL.objects.filter(added__lt=cls.Expired()).delete()

    def _set_code(self):
        if self.code is None and self.url:
            self.code = hashlib.sha1(
                '%s%s' % (time.time(), self.url)).hexdigest()[:16]

    def __repr__(self):
        return '<ShortURL(%s): %s>' % (self.code, self.url)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        self._set_code()

    def short_length(self):
        return 3 + len(settings.SITE_URL) + len(self.code)

    def short_url(self):
        return '%s/r/%s' % (settings.SITE_URL, self.code)

    def __str__(self):
        if self.short_length() < len(self.url):
            return self.short_url()
        else:
            return self.url

    def save(self):
        self._set_code()
        if self.short_length() < len(self.url):
            models.Model.save(self)
        return self
