from datetime import datetime

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from core.models import ActionEvent

from member.models import Member
from member.models import MemberGroup

@login_required
def list(request, group_techname=None):

    members = Member.objects.safe(request.user).prefetch_related('membergroups')

    if group_techname:
        members = members.filter(membergroups__techname=group_techname)
    
    # NOTE: Apparently concatinating lists of strings is really efficient.
    lines = []

    # Construct header. Things are set up this way for easy
    # commenting/uncommenting of particular fields, since needs are likely to
    # change over time. Same with the values, below.
    header_fields = [
        _('SSN'),
        #_('Name'),
        #_('Username'),
        #_('Email'),
        #_('Email wanted'),
        #_('Phone'),
        #_('Added'),
        #_('Groups'),
    ]
    lines.append('#%s' % ','.join(['"%s"' % field for field in header_fields]))

    for m in members:
        field_values = [
            m.ssn,
            #m.name,
            #m.username,
            #m.email,
            #m.email_wanted,
            #m.phone,
            #m.added,
            #u', '.join([g.name for g in m.membergroups.all()]),
        ]
        lines.append(','.join(['"%s"' % value for value in field_values]))

    timing = datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    if group_techname:
        filename = 'Members.%s.%s.csv' % (group_techname, timing)
    else:
        filename = 'Members.%s.csv' % timing

    ActionEvent(
        user=request.user,
        action='csv_export',
        action_details=group_techname if group_techname else _('All members'),
        affected_members=members
    ).save()

    response = HttpResponse("\n".join(lines), content_type='text/css; charset: utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response
