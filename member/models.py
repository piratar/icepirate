from django.db import models
from datetime import datetime
from group.models import Group

class Member(models.Model):
    kennitala = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=63)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    partake = models.BooleanField(default=False)
    added = models.DateTimeField(default=datetime.now)
    mailing = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group)

    def __unicode__(self):
        return self.name
