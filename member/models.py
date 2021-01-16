import hashlib
import time

from core import jaapi
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from datetime import timedelta

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
    legal_address = models.CharField(max_length=63, null=True)
    legal_zip_code = models.CharField(max_length=3, null=True)
    legal_municipality_code = models.CharField(max_length=5, null=True)
    legal_municipality = models.ForeignKey('Municipality', null=True, on_delete=models.SET_NULL)
    legal_zone = models.CharField(max_length=63, null=True)
    legal_country_code = models.CharField(max_length=2, null=True)
    legal_lookup_timing = models.DateTimeField(null=True)

    temporary_web_id = models.CharField(max_length=40, unique=True, null=True)
    temporary_web_id_timing = models.DateTimeField(null=True)

    membergroups = models.ManyToManyField('MemberGroup', related_name='members')

    class Meta:
        ordering = ['added', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Member, self).save(*args, **kwargs)

        # The mailing list is just a stepping stone toward membership, so when
        # someone becomes a member, they no longer need the mailing list.
        Subscriber.objects.filter(email=self.email).delete()

    # Updates the national registry information if, and only if it is outdated
    # according to settings.
    def ensure_national_registration_updated(self):
        updated = False

        threshold = timezone.now() - timedelta(
            days=settings.NATIONAL_REGISTRY_EXPIRATION_DAYS
        )
        if self.legal_lookup_timing is None or self.legal_lookup_timing < threshold:
            self.update_from_national_registry()
            updated = True

        return updated

    def update_from_national_registry(self, person_data=None):
        if person_data is None:
            person_data = jaapi.get_person(self.ssn)

        addr = person_data['permanent_address']

        try:
            municipality = Municipality.objects.get(code=addr['municipality'])
        except Municipality.DoesNotExist:
            municipality = None

        self.legal_name = person_data['name']
        self.legal_address = addr['street']['dative'] if addr['street'] else None
        self.legal_zip_code = addr['postal_code']
        self.legal_municipality_code = addr['municipality']
        self.legal_municipality = municipality
        self.legal_zone = addr['town']['dative'] if addr['town'] else None
        self.legal_country_code = addr['country']['code']
        self.legal_lookup_timing = timezone.now()

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


class Municipality(models.Model):
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['code']


class MemberGroup(models.Model):
    objects = SafetyManager()

    name = models.CharField(max_length=50, unique=True)
    techname = models.CharField(max_length=50, unique=True)
    # max_length 191 because of some MySQL indexing limitation.
    email = models.EmailField(max_length=191, unique=True)
    added = models.DateTimeField(default=datetime.now)

    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='membergroup_administrations')

    condition_municipalities = models.ManyToManyField('Municipality', related_name='membergroup_conditions')

    auto_subgroups = models.ManyToManyField(
        'MemberGroup',
        related_name='auto_parent_membergroups'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


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
