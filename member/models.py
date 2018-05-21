import hashlib
import time

from django.db import models
from django.conf import settings
from datetime import datetime

from group.models import Group


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

    email_wanted = models.BooleanField(default=False)
    phone = models.CharField(max_length=30, blank=True)
    partake = models.BooleanField(default=False)
    added = models.DateTimeField(default=datetime.now)
    mailing = models.BooleanField(default=False)
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

    groups = models.ManyToManyField(Group, related_name='members')

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

    def get_groups(self, parent_groups=True, location_groups=True):
        groups = set([])

        for group in self.groups.all():
            groups.add(group)
            if parent_groups:
                groups |= set(group.auto_parent_groups.all())

        if location_groups:
            for lc in self.get_location_codes():
                groups |= set(lc.auto_location_groups.all())

        return groups

    def email_sig(self):
        ts = '%x/' % time.time()
        return ts + hashlib.sha1('%s:%s%s:%s' % (
             settings.JSON_API_KEY, ts, self.email, settings.JSON_API_KEY
             )).hexdigest()

    def wasa2il_url(self, *args, **kwargs):
        from icepirate.utils import wasa2il_url
        return wasa2il_url(self, *args, **kwargs)
