from datetime import datetime

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from member.models import Member

@login_required
def list(request, group_techname):
    if group_techname:
        members = Member.objects.filter(groups__techname=group_techname)
    else:
        members = Member.objects.all()
    
    # NOTE: Apparently concatinating lists of strings is really efficient.
    lines = []

    lines.append('#"SSN","Name","Username","Email","Phone","Added","Municipality","Zip"')
    for m in members:
        line = '"%s","%s","%s","%s","%s","%s"' % (m.ssn, m.name, m.username, m.email, m.phone, m.added, m.legal_municipality_code, m.legal_zip_code)
        lines.append(line)

    if group_techname:
        filename = 'Members.%s.%s.csv' % (group_techname, datetime.now().strftime('%Y-%m-%d.%H-%M-%S'))
    else:
        filename = 'Members.%s.csv' % datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    response = HttpResponse("\n".join(lines), content_type='text/css; charset: utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response

