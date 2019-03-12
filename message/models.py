import datetime
import copy
import time
import hashlib

from markdown import markdown

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from icepirate.models import SafetyManager
from icepirate.utils import generate_unique_random_string, wasa2il_url
from locationcode.models import LocationCode
from member.models import Member


class Message(models.Model):
    objects = SafetyManager()

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
    membergroups = models.ManyToManyField('member.MemberGroup')
    groups_include_subgroups = models.BooleanField(default=True)
    groups_include_locations = models.BooleanField(default=False)
    locations = models.ManyToManyField(LocationCode, blank=True)

    wasa2il_usage = models.CharField(max_length=12,
        choices=WASA2IL_MEMBERSHIP_TYPES,
        default=WASA2IL_ANY)

    recipient_list = models.ManyToManyField(Member, related_name='recipient_list') # Constructed at time of processing
    deliveries = models.ManyToManyField(Member, related_name='deliveries', through='MessageDelivery') # Members already sent to
    author = models.ForeignKey(User) # User, not Member

    generate_html_mail = models.BooleanField(default=False)

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

        # Only superusers can see messages that should go to everyone.
        if self.send_to_all:
            self.full_administration = user.is_superuser
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
            if message.wasa2il_usage == message.WASA2IL_USERS:
                q = q.filter(username__isnull=False)
            elif message.wasa2il_usage == message.WASA2IL_NON_USERS:
                q = q.filter(username__isnull=True)
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

    def get_text_body(message, recipient):
        return message.get_bodies(recipient, with_html=False)[0]

    def get_html_body(message, recipient):
        return message.get_bodies(recipient, with_html=True)[1]

    def get_bodies(message, recipient, with_html=True):
        body, html_body = message.body, None

        for field in (
                'ssn', 'name', 'username', 'email', 'phone', 'added',
                'legal_name', 'legal_address',
                'legal_zip_code', 'legal_municipality_code'):
            data = unicode(getattr(recipient, field))
            body = body.replace('{{%s}}' % field, data)

        # When embedding the following URLs into e-mails, we force them to
        # count as verified; this e-mail effectively becomes a verification
        # mail in disguise.
        if '{{wasa2il_url}}' in body:
            data = wasa2il_url(recipient, verified=True)
            body = body.replace('{{wasa2il_url}}', data)
        if '{{wasa2il_url_short}}' in body:
            data = wasa2il_url(recipient, verified=True, shorten=True)
            body = body.replace('{{wasa2il_url_short}}', data)

        if message.generate_html_mail and with_html:
            html_body = markdown(body)

        rejection_body = None
        try:
            rejection_message = InteractiveMessage.objects.get(
                interactive_type='reject_email_messages')

            if not recipient.temporary_web_id:
                random_string = generate_unique_random_string()
                recipient.temporary_web_id = random_string
                recipient.save()

            rejection_body = rejection_message.produce_links(
                recipient.temporary_web_id)

            body += '\n\n------------------------------\n'
            body += rejection_body

        except InteractiveMessage.DoesNotExist:
            pass

        if html_body:
            try:
                html_template = InteractiveMessage.objects.get(
                    interactive_type='email_html_template')

                html_body = html_template.render_body(
                    recipient.temporary_web_id,
                    message_content=html_body,
                    footer_content=rejection_body)

            except InteractiveMessage.DoesNotExist:
                # If we have no HTML template, hard-code the basics.
                html_body += (
                    '\n<div class="icepirate_footer"><hr>\n%s\n</div>\n'
                    % markdown(rejection_body))

            html_body = (
                '<html><body>\n%s\n</body></html>' % html_body
                ).replace('\r', '').replace('\n', '\r\n')

        return body, html_body or None


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
        ('email_html_template', 'Email HTML template'),
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
        'email_html_template': {
            'description': 'Use the strings {{message_content}} and {{footer_content}} to place\nthe actual message content and rejection links.',
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

    def produce_links(self, random_string, body=None, raw=False):
        result = body or self.body

        for link_name in InteractiveMessage.INTERACTIVE_TYPES_DETAILS[
                self.interactive_type]['links']:
            short_link = ShortURL(url='%s/message/mailcommand/%s/%s/%s/' % (
                settings.SITE_URL,
                self.interactive_type,
                link_name,
                random_string))
            short_link.save()
            link = str(short_link)
            if not raw:
                link = '<%s>' % link
            result = result.replace('{{%s}}' % link_name, link)

        return result

    def render_body(self, random_string, **data):
        result = self.body

        assert('message_content' in data)
        for data_name in data:
            result = result.replace(
                '{{%s}}' % data_name, data[data_name] or '')

        if random_string:
            return self.produce_links(random_string, body=result, raw=True)
        else:
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
