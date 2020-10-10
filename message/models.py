import datetime
import copy
import time
import hashlib

from markdown import markdown

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import CASCADE
from django.db.models import PROTECT
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

from icepirate.models import SafetyManager
from icepirate.utils import generate_random_string
from icepirate.utils import quick_mail
from member.models import Member
from member.models import MemberGroup
from member.models import Subscriber

from core.loggers import log_mail


class Message(models.Model):
    objects = SafetyManager()

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField(null=True, blank=True)

    send_to_all = models.BooleanField(default=True)
    include_mailing_list = models.BooleanField(default=True)
    membergroups = models.ManyToManyField('member.MemberGroup', related_name='messages')
    groups_include_subgroups = models.BooleanField(default=True)

    author = models.ForeignKey(User, on_delete=PROTECT)

    ready_to_send = models.BooleanField(default=False) # Should this message be processed?

    sending_started = models.DateTimeField(null=True) # Marked when processing beings
    sending_complete = models.DateTimeField(null=True) # Marked when processing ends

    # Number of intended recipients, before bulk send.
    recipient_count = models.IntegerField(default=0)
    # Number of recipients that message has already been sent to. When bulk
    # send is complete, this number should match `recipient_count`.
    recipient_count_complete = models.IntegerField(default=0)

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


    '''
    Returns a list of Member and Subscriber objects, collectively called
    "recipients". Recipients are expected to have the fields `email` and
    `temporary_web_id`.
    '''
    def get_recipients(self):
        # List to be returned.
        recipients = []

        ################
        # Get members. #
        ################

        members = Member.objects.filter(
            # NOTE: `email_wanted` is the post-GDPR field that should become
            # the only one at some point. The `email_unwanted` field is from
            # the pre-GDPR days when we only explicitly recorded those who had
            # rejected email communication. The post-GDPR mindset is that
            # people should preferably explicitly state their will to receive
            # mail. When `email_wanted` (post-GDPR) is None, however, the
            # member has not stated anything at all, and we include them in
            # email communication on the grounds that it is to protect their
            # right as members to have knowledge of and access to the various
            # democratic processes that membership grants. In fact, it could
            # be argued that receiving email communication is the most basic
            # function of being a member in the first place, and in many cases
            # the only point.
            #
            # Still, all registration mechanisms should ask the member about
            # this, so the state of email_wanted=None should become ever-more
            # rare as more members answer the question explicitly at some
            # point, since no new members are registered without being asked
            # about this.
            Q(email_wanted=True)
            | Q(email_wanted=None, email_unwanted=False)
        )

        if not self.send_to_all:
            if self.groups_include_subgroups:
                # Find not only the groups that the message is intended to,
                # but also the subgroups of those groups.
                groups = MemberGroup.objects.filter(
                    Q(messages=self)
                    | Q(auto_parent_membergroups__messages=self)
                ).distinct()
            else:
                groups = MemberGroup.objects.filter(messages=self)

            members = members.filter(membergroups__in=groups).distinct()

        recipients += members

        ####################
        # Get Subscribers. #
        ####################

        # Add subscribers if requested.
        if self.include_mailing_list:
            recipients += Subscriber.objects.filter(email_verified=True)

        return recipients


    '''
    Sends the message to all intended recipients, keeping track of those
    already sent to, so that sending can be stopped and resumed at will and
    continued on failure. Also makes sure that every target has a
    `temporary_web_id` for identification when communicating back.
    '''
    def send_bulk(self):

        # Get the Member and Subscriber objects we'll be sending to.
        recipients = self.get_recipients()

        # We'll be reporting this back to the calling function so that an
        # iterating caller may know how much is left. This must figured out
        # before we remove recipients already delievered to.
        self.recipient_count = len(recipients)

        # Declare that we've started the show.
        self.sending_started = timezone.now()
        self.save()

        # Remove recipients that have already received the message, which may
        # happen if a bulk sending is cancelled or fails before completing.
        for delivery in self.deliveries.select_related('member', 'subscriber'):
            if delivery.member is not None:
                recipients.remove(delivery.member)
            elif delivery.subscriber is not None:
                recipients.remove(delivery.subscriber)

        # Make sure that any Member and Subscriber have `temporary_web_id`
        # values for communicating back. It is very rare that they are lacking
        # and basically might only affect very old memberships or if someone
        # is registered manually by an administrator. Recipients are either
        # Member or Subscriber models and are expected to have both an `email`
        # and `temporary_web_id` field.
        for recipient in recipients:
            if recipient.temporary_web_id is None:
                recipient.temporary_web_id = generate_random_string()
                recipient.save()

        # Number of recipients left. This is different from `recipient_count`,
        # which describes the total number of recipients intended altogether.
        # Some recipients may already have been sent to in a previous run and
        # this number takes that into account. This and `recipient_count` will
        # be the same if this is the first attempt at running the bulk send.
        recipient_count_remaining = len(recipients)

        # If sending to any recipient fails, this will be switched to True and
        # the message will not be marked as complete. On future runs of this
        # function, an attempt will be made to send to those recipients who we
        # previously failed sending to. Only when we've successfully sent to
        # the entire list of recipients with this still remaining False
        # afterwards, do we mark the processing of the message as complete,
        # then applying clean-up measures.
        something_failed = False

        for i, recipient in enumerate(recipients):

            # Attempt to send the message.
            success = self.send(recipient)

            # Note the results for determining when the message has been
            # successfully processed.
            if success:
                with transaction.atomic():
                    delivery = MessageDelivery(message=self)
                    if type(recipient) is Member:
                        delivery.member = recipient
                    elif type(recipient) is Subscriber:
                        delivery.subscriber = recipient
                    delivery.save()

                    # We'll also keep track of this so that the web interface
                    # can keep track of progress. Heavier on the script, but
                    # easier on the interface, and we care more about the user
                    # experience than making sure that emails get completed
                    # some microseconds sooner. Bulk sending must be assumed
                    # to take a while anyway.
                    self.recipient_count_complete += 1
                    self.save()
            else:
                something_failed = True

            # Report back the status to a calling function.
            yield i+1, recipient_count_remaining, recipient.email, success

        # Clean up, if everything seems to have worked.
        if not something_failed:
            self.sending_complete = timezone.now()
            self.save()

            # No more need for delivery objects.
            MessageDelivery.objects.filter(message=self).delete()


    '''
    Sends the message to a single email address, taking care of
    unsubscribe-links and logging. Bulk sending is managed by `send_bulk()`.

    Takes the single argument `recipient`, which is expected to have `email`
    and `temporary_web_id` fields, like Member or Subscriber objects.
    '''
    def send(self, recipient):
        body = self.body

        # Append the portion of the email that offers the user to unsubscribe,
        # if that message ("reject_email_messages") has been configured and a
        # temporary web ID is provided to fill the link.
        if recipient.temporary_web_id is not None:
            unsubscription = InteractiveMessage.objects.filter(
                interactive_type='reject_email_messages'
            ).first()

            if unsubscription:
                body += '\n\n---\n'
                body += unsubscription.produce_links(recipient.temporary_web_id)

        try:
            # Actually send.
            quick_mail(
                to=recipient.email,
                subject=self.subject,
                body=body,
                from_email=self.from_address,
                subject_prefix=None
            )

            # Log and notify calling function of success.
            log_mail(recipient.email, self)
            return True

        except Exception as ex:
            # Log and notify calling function of failure.
            log_mail(recipient.email, self, ex)
            return False

    class Meta:
        ordering = ['added']


class MessageDelivery(models.Model):
    message = models.ForeignKey(Message, on_delete=CASCADE, related_name='deliveries')
    member = models.ForeignKey('member.Member', null=True, on_delete=CASCADE)
    subscriber = models.ForeignKey('member.Subscriber', null=True, on_delete=CASCADE)
    timing = models.DateTimeField(default=timezone.now)


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

    from_address = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=300, default='[%s] ' % settings.EMAIL_SUBJECT_PREFIX)
    body = models.TextField(null=True, blank=True)

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
            interactive_type__in=required_types
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
        try:
            # Fill the message template with appropriate links if requested.
            if type(random_string) is str:
                body = self.produce_links(random_string)
            else:
                body = self.body

            # Check if the email belongs to a Member.
            try:
                member = Member.objects.get(email=email)
            except Member.DoesNotExist:
                member = None

            # Actually send the prepared message.
            quick_mail(email, self.subject, body)

            # Log the success.
            log_mail(email, self)

        except Exception as ex:
            # Log the failure.
            log_mail(email, self, ex)


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
