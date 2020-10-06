import hashlib
import time

from django.db import models
from django.conf import settings
from datetime import datetime

from icepirate.models import SafetyManager


class Member(models.Model):
    objects = SafetyManager()

    ssn = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=63)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)

    # NOTE/IMPORTANT: The `email_unwanted` field is deprecated and should
    # never be used in code. It is from the time when consent for receiving
    # email was assumed from the registration of a member. As a result of the
    # General Data Protection Regulation however, explicit consent is required
    # and marked in the `email_wanted` field. The `email_unwanted` field is
    # only retained to keep information about who had specifically rejected
    # emails before the GDPR took effect. By keeping this field, it's possible
    # to look up members who have not explicitly consented to receiving email,
    # but had also not specifically rejected it before GDPR. This may be
    # useful during the transition to GDPR-compliance, but at some point this
    # field will become useless and shall then be removed.
    email_unwanted = models.BooleanField(default=False)

    # Null means question unanswered. True/False dictate consent.
    email_wanted = models.NullBooleanField(default=None)

    phone = models.CharField(max_length=30, blank=True)
    added = models.DateTimeField(default=datetime.now)
    verified = models.BooleanField(default=False)
    auth_token = models.CharField(max_length=100, unique=True, null=True)
    auth_timing = models.DateTimeField(null=True)

    legal_name = models.CharField(max_length=63)
    legal_address = models.CharField(max_length=63)
    legal_zip_code = models.CharField(max_length=3, null=True)
    legal_municipality_code = models.CharField(max_length=5, null=True)
    legal_zone = models.CharField(max_length=63, null=True)
    legal_lookup_timing = models.DateTimeField(null=True)

    temporary_web_id = models.CharField(max_length=40, unique=True, null=True)
    temporary_web_id_timing = models.DateTimeField(null=True)

    membergroups = models.ManyToManyField('MemberGroup', related_name='members')

    class Meta:
        ordering = ['added', 'name']

    def __str__(self):
        return self.name

    def get_membergroups(self, parent_membergroups=True):
        membergroups = set([])

        for membergroup in self.membergroups.all():
            membergroups.add(membergroup)
            if parent_membergroups:
                membergroups |= set(membergroup.auto_parent_membergroups.all())

        return membergroups

    def email_sig(self):
        ts = '%x/' % time.time()
        return ts + hashlib.sha1('%s:%s%s:%s' % (
             settings.JSON_API_KEY, ts, self.email, settings.JSON_API_KEY
             )).hexdigest()


class MemberGroup(models.Model):
    objects = SafetyManager()

    name = models.CharField(max_length=50, unique=True)
    techname = models.CharField(max_length=50, unique=True)
    # max_length 191 because of some MySQL indexing limitation.
    email = models.EmailField(max_length=191, unique=True)
    added = models.DateTimeField(default=datetime.now)

    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='membergroup_administrations')

    auto_subgroups = models.ManyToManyField(
        'MemberGroup',
        related_name='auto_parent_membergroups'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_members(self, subgroups=True):

        membergroup_ids = set([self.id])
        if subgroups:
            membergroup_ids |= set(self.auto_subgroups.values_list('id', flat=True))
        mQs = models.Q(membergroups__id__in = membergroup_ids)

        return Member.objects.filter(mQs).distinct()


class Subscriber(models.Model):
    '''
    A Subscriber is only subscribed to email announcements but is not a
    Member. It is implemented as a separate model from Member, even though it
    contains similar basic info, because when using the Member table, a
    developer/user should be able to assume that they are dealing with an
    actual Member. Requiring developers and users to make a distinction
    between Members and Subscribers at all times when dealing with the data
    has more cons than pros.

    When someone with a Subscriber's email address becomes a full Member, they
    should be deleted as a Subscriber and added as a Member.

    Note that Subscriber should never become a feature-rich object.
    Subscribers are expected to become Members in order to cutomize anything,
    since keeping track of two different notions of Members only offers
    unnecessary complications. Subscribers are not Members in any way and
    should never be considered half-Members or a different type of Member,
    they simply receive announcements and have no control or options other
    than upgrading to a full Member, or quitting their subscriptions.
    '''

    email = models.CharField(max_length=75, unique=True)
    email_verified = models.BooleanField(default=False)
    email_verified_timing = models.DateTimeField(null=True)
    temporary_web_id = models.CharField(max_length=40, unique=True, null=True)
    temporary_web_id_timing = models.DateTimeField(null=True)

    # Database creation timing, NOT reflecting Member.added, which indicates
    # when the Member joined and may be copied from other sources, whereas
    # this is strictly for database housekeeping.
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s (%s)' % (
            self.email,
            'verified' if self.email_verified else 'unverified'
        )
