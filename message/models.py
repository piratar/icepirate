import datetime
import copy
import time
import hashlib

from markdown import markdown

from django.conf import settings
from django.db import models
from django.db.models import CASCADE
from django.db.models import PROTECT
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from icepirate.models import SafetyManager
from icepirate.utils import generate_random_string
from icepirate.utils import quick_mail
from locationcode.models import LocationCode
from member.models import Member


class Message(models.Model):
    objects = SafetyManager()

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField(null=True, blank=True)

    send_to_all = models.BooleanField(default=True)
    membergroups = models.ManyToManyField('member.MemberGroup')
    groups_include_subgroups = models.BooleanField(default=True)
    groups_include_locations = models.BooleanField(default=False)
    locations = models.ManyToManyField(LocationCode, blank=True)

    recipient_list = models.ManyToManyField(Member, related_name='recipient_list') # Constructed at time of processing
    deliveries = models.ManyToManyField(Member, related_name='deliveries', through='MessageDelivery') # Members already sent to
    author = models.ForeignKey(User, on_delete=PROTECT)

    ready_to_send = models.BooleanField(default=False) # Should this message be processed?

    sending_started = models.DateTimeField(null=True) # Marked when processing beings
    sending_complete = models.DateTimeField(null=True) # Marked when processing ends

    added = models.DateTimeField(default=timezone.now) # Automatic, un-editable field

    # Determines whether the user is an admin over every single membergroup
    # that the message is sent to. Only such users can edit or delete such
    # messages. Will also return True if user is a superuser, because
    # superusers can do anything they want.
    #
    # Usage: In a view, call this function on a message with the currently
    # logged in user as an argument. From that point on, you may check
    # `message.full_administration` to retrieve the result. The value is also
    # returned so that the function can be used independently without regard
    # for the self.full_administration property.
    def populate_full_administration(self, user):

        if user.is_superuser:
            # Superusers always have full administration.
            self.full_administration = True
            return self.full_administration
        elif self.send_to_all:
            # Messages sent to everyone required superuser privileges.
            self.full_administration = False
            return self.full_administration

        # Otherwise, we'll have to make sure that the user is a member of
        # every group to which the message is addressed to.
        user_mgs = user.membergroup_administrations.all()
        message_mgs = self.membergroups.all()
        for message_mg in message_mgs:
            if message_mg not in user_mgs:
                self.full_administration = False
                return self.full_administration

        self.full_administration = True
        return self.full_administration


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
                recipients.extend(rcpt_filter(membergroup.get_members(
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

    def get_bodies(message, recipient):
        body = message.body

        for field in (
                'ssn', 'name', 'username', 'email', 'phone', 'added',
                'legal_name', 'legal_address',
                'legal_zip_code', 'legal_municipality_code'):
            data = str(getattr(recipient, field))
            body = body.replace('{{%s}}' % field, data)

        rejection_body = None
        try:
            rejection_message = InteractiveMessage.objects.get(
                interactive_type='reject_email_messages')

            if not recipient.temporary_web_id:
                random_string = generate_random_string()
                recipient.temporary_web_id = random_string
                recipient.save()

            rejection_body = rejection_message.produce_links(
                recipient.temporary_web_id)

            body += '\n\n------------------------------\n'
            body += rejection_body

        except InteractiveMessage.DoesNotExist:
            pass

        return body


class MessageDelivery(models.Model):
    message = models.ForeignKey(Message, on_delete=CASCADE)
    member = models.ForeignKey(Member, null=True, on_delete=models.SET_NULL)
    email = models.CharField(max_length=75)
    timing_start = models.DateTimeField(default=timezone.now)
    timing_end = models.DateTimeField(null=True)


class InteractiveMessage(models.Model):

    INTERACTIVE_TYPES = (
        ('registration_received', 'Registration received'),
        ('registration_confirmed', 'Registration confirmed'),
        ('reject_email_messages', 'Reject mail messages'),
        ('mailinglist_confirmation', 'Mailing list confirmation'),
        ('remind_membership', 'Reminder of existing membership'),
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
        'mailinglist_confirmation': {
            'description': 'Use the strings {{confirm}} and {{reject}}\nto place confirmation and rejection links.',
            'links': ('confirm', 'reject'),
        },
    }

    interactive_type = models.CharField(max_length=60, choices=INTERACTIVE_TYPES)
    active = models.BooleanField(default=True)

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField(null=True, blank=True)

    deliveries = models.ManyToManyField(Member, related_name='interactive_deliveries', through='InteractiveMessageDelivery')
    author = models.ForeignKey(User, on_delete=PROTECT)

    added = models.DateTimeField(default=timezone.now) # Automatic, un-editable field

    '''
    Takes a list of required interactive message types, to make sure that the
    administrator has configured them when they are required.
    '''
    @staticmethod
    def require_types(required_types):

        if not type(required_types) is list:
            raise Exception(
                'Function InteractiveMessage.required_types needs one list of strings'
            )

        interactive_types_found = InteractiveMessage.objects.filter(
            interactive_type__in=required_types,
            active=True
        ).distinct().count()
        if len(required_types) != interactive_types_found:
            raise Exception(
                'Some of required interactive message types not configured yet: %s' % required_types
            )

    '''
    Sends the interactive message to the designated email with a given random
    string for the recipient to communicate back, while handling delivery
    logging. The calling function is responsible for database management of
    the random string.
    '''
    def send(self, email, random_string=None):
        # Fill the message template with the appropriate links if requested.
        if type(random_string) is str:
            body = self.produce_links(random_string)
        else:
            body = self.body

        # Check if the email belongs to a Member.
        try:
            member = Member.objects.get(email=email)
        except Member.DoesNotExist:
            member = None

        # Save the delivery message before sending.
        delivery = InteractiveMessageDelivery(
            interactive_message=self,
            member=member,
            email=email,
            timing_start=timezone.now()
        )
        delivery.save()

        # Actually send the prepared message.
        quick_mail(email, self.subject, body)

        # Note in the message delivery that the message was successfully sent.
        delivery.timing_end = timezone.now()
        delivery.save()


    def produce_links(self, random_string):
        result = self.body

        for link_name in InteractiveMessage.INTERACTIVE_TYPES_DETAILS[
                self.interactive_type]['links']:
            short_link = ShortURL(url='%s/message/mailcommand/%s/%s/%s/' % (
                settings.SITE_URL,
                self.interactive_type,
                link_name,
                random_string))
            short_link.save()
            link = str(short_link)
            link = '<%s>' % link
            result = result.replace('{{%s}}' % link_name, link)

        return result

    class Meta:
        ordering = ['interactive_type', 'added']


class InteractiveMessageDelivery(models.Model):
    interactive_message = models.ForeignKey('InteractiveMessage', on_delete=CASCADE)
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
                str('%s%s' % (time.time(), self.url)).encode('utf-8')
            ).hexdigest()[:16]

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
