# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models

class ActionEvent(models.Model):
    ACTIONS = (
        ('member_add', 'Member added'),
        ('member_edit', 'Member edited'),
        ('member_delete', 'Member deleted'),
        ('member_view', 'Member viewed'),
        ('member_search', 'Member search'),
    )

    # The user performing the action.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='access_events')

    # When the action was performed.
    timing = models.DateTimeField(auto_now_add=True)

    # Example: 'member_search', 'member_view' etc.
    action = models.CharField(max_length=50, choices=ACTIONS)

    # More detail on the action taken, when appropriate. For example, the
    # search string of a member search.
    action_details = models.CharField(max_length=500, null=True)

    # A list of members affected by the action. For example, the search result
    # of a member search. Note that when a member is deleted, they are also
    # deleted from here.
    affected_members = models.ManyToManyField('member.Member')

    # Auto-populated field for keeping track of how many users are needed.
    # Using this field is preferable to using `affected_members` in displaying
    # events because we prefer displaying statistics rather than personal
    # data, even when personal data needs to be retained. This also retains
    # the number of affected users instead of the `affected_members` field,
    # because members are removed from that field upon their deletion.
    affected_member_count = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        # Save the affected members temporarily for the save-function to have
        # access to them. This is to support `affected_members` directly when
        # creating a single action event with a one-liner.
        if 'affected_members' in kwargs:
            self.temp_affected_members = kwargs.pop('affected_members')

        super(ActionEvent, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if hasattr(self, 'temp_affected_members'):
            # len() used instead to save on hit to the database.
            self.affected_member_count = len(self.temp_affected_members)

        # Only one user is ever deleted at a time, so we'll know that the
        # number of affected users was 1, even though we can't store
        # information on the deleted user for privacy reasons.
        if self.action == 'member_delete':
            self.affected_member_count = 1

        super(ActionEvent, self).save(*args, **kwargs)

        if hasattr(self, 'temp_affected_members'):
            for m in self.temp_affected_members:
                self.affected_members.add(m)

    def __str__(self):
        message = '%s: User "%s", action "%s", affected users: %d' % (
            self.timing.strftime('%Y-%m-%d %H:%M:%S'),
            self.user.username,
            self.action,
            self.affected_member_count
        )

        if self.action_details:
            message += ', details: "%s"' % self.action_details

        return message

    class Meta:
        ordering = ['-timing']
