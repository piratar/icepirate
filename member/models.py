from django.db import models
from datetime import datetime
from group.models import Group

class Member(models.Model):
    ssn = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=63)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    partake = models.BooleanField(default=False)
    added = models.DateTimeField(default=datetime.now)
    mailing = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    auth_token = models.CharField(max_length=100, unique=True, null=True)
    auth_timing = models.DateTimeField(null=True)

    groups = models.ManyToManyField(Group)

    class Meta:
        ordering = ['added']

    def __unicode__(self):
        return self.name
