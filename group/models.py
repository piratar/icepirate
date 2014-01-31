from django.db import models
from datetime import datetime

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)
    techname = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    added = models.DateTimeField(default=datetime.now)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name
