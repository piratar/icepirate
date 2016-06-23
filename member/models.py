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

class LocationCode(models.Model):
    location_code = models.CharField(max_length=20, unique=True)
    location_name = models.CharField(max_length=200)

    def __unicode__(self):
        if self.location_name:
            return u'%s (%s)' % (self.location_code, self.location_name)
        return u'%s' % self.location_code

    def get_members(self):
        if ':' not in self.location_code:
            return []

        # FIXME: This code is ugly, magic strings are bad.
        #        Member should be refactored to use LocationCode directly,
        # instead of having Iceland-specific fields (legal_municipality_code
        # and legal_zip_code). The Iceland-specific codes and import logic
        # belong in the national registry gateway and the load_icelandic_data
        # management command.
        #
        code = self.location_code.split(':')[1]
        if self.location_code.startswith('pnr:'):
            return Member.objects.filter(legal_zip_code=code)
        elif self.location_code.startswith('svfnr:'):
            return Member.objects.filter(legal_municipality_code=code)
