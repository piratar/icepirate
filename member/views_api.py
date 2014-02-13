import json

from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from member.models import Member
from group.models import Group

def member_to_dict(member):
    result = {
        'kennitala': member.kennitala,
        'name': member.name,
        'username': member.username,
        'email': member.email,
        'phone': member.phone,
        'partake': member.partake,
        'added': member.added.strftime('%Y-%m-%d %H:%M:%S'),
        'mailing': member.mailing,
        'verified': member.verified,
        'groups': []
    }
    result['groups'] = [g.techname for g in member.groups.all()]
    return result

@login_required
def list(request):
    members = Member.objects.all().order_by('added')

    data = []
    for member in members:
        data.append(member_to_dict(member))

    response_data = {
        'success': True,
        'meta': {
            'count': len(data)
        },
        'data': data
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')

@login_required
def filter(request, field, searchstring):
    members = []

    if field == 'name':
        members = Member.objects.filter(name__icontains=searchstring)
    elif field == 'username':
        members = Member.objects.filter(username__icontains=searchstring)
    elif field == 'email':
        members = Member.objects.filter(email__icontains=searchstring)
    else:
        raise Http404

    data = []
    for member in members:
        data.append(member_to_dict(member))

    response_data = {
        'success': True,
        'meta': {
            'count': len(data)
        },
        'data': data
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')

@login_required
def get(request, field, searchstring):
    if field == 'name':
        member = get_object_or_404(Member, name=searchstring)
    elif field == 'username':
        member = get_object_or_404(Member, username=searchstring)
    elif field == 'kennitala':
        member = get_object_or_404(Member, kennitala=searchstring)
    else:
        raise Http404

    response_data = {
        'success': True,
        'data': member_to_dict(member)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')


