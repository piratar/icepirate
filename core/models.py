# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import CASCADE

from member.models import Member

class ActionEvent(models.Model):
    ACTIONS = (
        ('member_add', 'Member added'),
        ('member_edit', 'Member edited'),
        ('member_delete', 'Member deleted'),
        ('member_view', 'Member viewed'),
        ('member_search', 'Member search'),
    )

    # The user performing the action.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='access_events', on_delete=CASCADE)

    # When the action was performed.
    timing = models.DateTimeField(auto_now_add=True)

    # Example: 'member_search', 'member_view' etc.
    action = models.CharField(max_length=50, choices=ACTIONS)

    # More detail on the action taken, when appropriate. For example, the
    # search string of a member search.
    action_details = models.CharField(max_length=500, null=True)

    # A comma-separated list of member row IDs that were affected by the
    # action. Information on the affected members is preserved in this manner
    # for two reasons. One is performance, because adding thousands of records
    # every time something is done that affects the entire member database
    # takes a very long time. The 2nd is to retain the IDs of those who were
    # affected, even after they've been deleted from the database. That way,
    # the data is in some sense more accurate, even though no information on
    # the deleted member's information can be retrieved.
    affected_member_ids = models.TextField(default='')

    # Auto-populated field for keeping track of how many users are needed.
    # Using this field is preferable to using `affected_members` in displaying
    # events because we prefer displaying statistics rather than personal
    # data, even when personal data needs to be retained. This also retains
    # the number of affected users instead of the `affected_members` field,
    # because members are removed from that field upon their deletion.
    affected_member_count = models.IntegerField(default=0)

    # Returns the affected members, as objects.
    def affected_members(self):
        if self.affected_member_ids == '':
            return []
        else:
            return Member.objects.filter(id__in=[int(m_id) for m_id in self.affected_member_ids.split(',')])

    def __init__(self, *args, **kwargs):
        # Must happen before super() because super() will not want
        # affected_members in the kwargs.
        if 'affected_members' in kwargs:
            affected_members = kwargs.pop('affected_members')
        else:
            affected_members = None

        super(ActionEvent, self).__init__(*args, **kwargs)

        # Must happen after super() because super() will initialize
        # self.affected_member_ids.
        if affected_members is not None:
            self.affected_member_ids = ','.join([str(m.id) for m in affected_members])

    def save(self, *args, **kwargs):
        # Only one user is ever deleted at a time, so we'll know that the
        # number of affected users was 1, even though we can't store
        # information on the deleted user for privacy reasons.
        if self.action == 'member_delete':
            self.affected_member_count = 1
        else:
            # Otherwise, we'll count the affected members, assuming there are any.
            if self.affected_member_ids:
                self.affected_member_count = len(self.affected_member_ids.split(','))
            else:
                self.affected_member_count = 0

        super(ActionEvent, self).save(*args, **kwargs)

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
