from datetime import datetime

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from group.models import Group
from member.models import Member
from locationcode.models import LocationCode

@login_required
def list(request, group_techname=None, location_code=None, combined=False):
    if group_techname:
        group = Group.objects.get(techname=group_techname)
        if combined:
            members = group.get_members()
        else:
            members = group.members.all()
    elif location_code:
        location_code = LocationCode.objects.get(location_code=location_code)
        members = location_code.get_members()
    else:
        members = Member.objects.all()
    
    # NOTE: Apparently concatinating lists of strings is really efficient.
    lines = []

    lines.append('#"SSN","Name","Username","Email","Email wanted","Phone","Added","Groups"')
    for m in members:
        line = '"%s","%s","%s","%s","%s","%s","%s","%s"' % (
            m.ssn,
            m.name,
            m.username,
            m.email,
            m.email_wanted,
            m.phone,
            m.added,
            u', '.join([g.name for g in m.groups.all()])
        )
        lines.append(line)

    if group_techname:
        fmt = 'Members-Combined.%s.%s.csv' if combined else 'Members.%s.%s.csv'
        filename = fmt % (group_techname, datetime.now().strftime('%Y-%m-%d.%H-%M-%S'))
    elif location_code:
        loc_name = unicode(location_code).replace(':', '-').replace(' ', '_')
        filename = 'Members-%s.%s.csv' % (loc_name, datetime.now().strftime('%Y-%m-%d.%H-%M-%S'))
    else:
        filename = 'Members.%s.csv' % datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    response = HttpResponse("\n".join(lines), content_type='text/css; charset: utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response

