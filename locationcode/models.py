from django.db import models


class LocationCode(models.Model):
    location_code = models.CharField(max_length=20, unique=True)
    location_name = models.CharField(max_length=200)

    auto_location_codes = models.ManyToManyField('LocationCode')

    def __unicode__(self):
        if self.location_name:
            text = u'%s (%s)' % (self.location_name, self.location_code)
        else:
            text = u'%s' % self.location_code
        return text

    def get_member_model_Qs(self):
        codes = ([self.location_code] + list(
            self.auto_location_codes.values_list('location_code', flat=True)))

        # FIXME: This code is ugly, magic strings are bad.
        #        Member should be refactored to use LocationCode directly,
        # instead of having Iceland-specific fields (legal_municipality_code
        # and legal_zip_code). The Iceland-specific codes and import logic
        # belong in the national registry gateway and the load_icelandic_data
        # management command.
        #
        zips = [c.split(':')[1] for c in codes if c.startswith('pnr:')]
        muns = [c.split(':')[1] for c in codes if c.startswith('svfnr:')]
        return (
            models.Q(legal_municipality_code__in=muns) |
            models.Q(legal_zip_code__in=zips))

    def get_members(self):
        from member.models import Member
        return Member.objects.filter(self.get_member_model_Qs()).distinct()
