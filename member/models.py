import hashlib
import time

from django.db import models
from django.conf import settings
from datetime import datetime

from locationcode.models import LocationCode


class Member(models.Model):
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
    # FIXME: The following two fields should be replaced by LocationCode,
    #        see comment below in the LocationCode class.
    legal_municipality_code = models.CharField(max_length=5, null=True)
    legal_zone = models.CharField(max_length=63, null=True)
    legal_lookup_timing = models.DateTimeField(null=True)

    temporary_web_id = models.CharField(max_length=40, unique=True, null=True)
    temporary_web_id_timing = models.DateTimeField(null=True)

    membergroups = models.ManyToManyField('MemberGroup', related_name='members')

    class Meta:
        ordering = ['added', 'name']

    def __unicode__(self):
        return self.name

    def get_location_codes(self):
        from locationcode.models import LocationCode
        codes = ['svfnr:%s' % self.legal_municipality_code,
                 'pnr:%s' % self.legal_zip_code]
        return LocationCode.objects.filter(
            models.Q(location_code__in=codes) |
            models.Q(auto_location_codes__location_code__in=codes)
            ).distinct()

    def get_membergroups(self, parent_membergroups=True, location_membergroups=True):
        membergroups = set([])

        for membergroup in self.membergroups.all():
            membergroups.add(membergroup)
            if parent_membergroups:
                membergroups |= set(membergroup.auto_parent_membergroups.all())

        if location_membergroups:
            for lc in self.get_location_codes():
                membergroups |= set(lc.auto_location_membergroups.all())

        return membergroups

    def email_sig(self):
        ts = '%x/' % time.time()
        return ts + hashlib.sha1('%s:%s%s:%s' % (
             settings.JSON_API_KEY, ts, self.email, settings.JSON_API_KEY
             )).hexdigest()

    def wasa2il_url(self, *args, **kwargs):
        from icepirate.utils import wasa2il_url
        return wasa2il_url(self, *args, **kwargs)


class MemberGroup(models.Model):
    COMBINATION_METHODS = (
        ('union', 'Union'),
        ('intersection', 'Intersection')
    )

    name = models.CharField(max_length=50, unique=True)
    techname = models.CharField(max_length=50, unique=True)
    # max_length 191 because of some MySQL indexing limitation.
    email = models.EmailField(max_length=191, unique=True)
    added = models.DateTimeField(default=datetime.now)

    auto_subgroups = models.ManyToManyField(
        'MemberGroup',
        related_name='auto_parent_membergroups'
    )
    auto_locations = models.ManyToManyField(
        LocationCode,
        related_name='auto_location_membergroups'
    )
    combination_method = models.CharField(
        max_length=30,
        verbose_name="Combination method",
        choices=COMBINATION_METHODS,
        default=COMBINATION_METHODS[0][0]
    )

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_members(self, subgroups=True, locations=True):

        membergroup_ids = set([self.id])
        if subgroups:
            membergroup_ids |= set(self.auto_subgroups.values_list('id', flat=True))
        mQs = models.Q(membergroups__id__in = membergroup_ids)

        if locations:
            for locCode in self.auto_locations.all():
                if self.combination_method == 'intersection':
                    mQs &= locCode.get_member_model_Qs()
                else:
                    mQs |= locCode.get_member_model_Qs()

        return Member.objects.filter(mQs).distinct()
