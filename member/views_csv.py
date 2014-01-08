from datetime import datetime

from django.http import HttpResponse

from django.contrib.auth.decorators import login_required

from member.models import Member

@login_required
def list(request):
    members = Member.objects.all()
    
    # NOTE: Apparently concatinating lists of strings is really efficient.
    lines = []

    lines.append('#"CitizenNr","Name","Username","Email","Phone","Added"')
    for m in members:
        line = '"%s","%s","%s","%s","%s","%s"' % (m.kennitala, m.name, m.username, m.email, m.phone, m.added)
        lines.append(line)

    filename = 'Piratar-members-%s.csv' % datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    response = HttpResponse("\n".join(lines), content_type='text/css; charset: utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response

