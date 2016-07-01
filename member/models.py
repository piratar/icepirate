from django.db import models
from datetime import datetime

from group.models import Group


class Member(models.Model):
    ssn = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=63)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_unwanted = models.BooleanField(default=False)
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
