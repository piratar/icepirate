import json
import time

from django.conf import settings
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from icepirate.utils import json_error

from member.models import Member
from group.models import Group

def require_login_or_key(request):
    return request.user.is_authenticated() or request.GET.get('json_api_key') == settings.JSON_API_KEY

def member_to_dict(member):

    result = {
        'ssn': member.ssn,
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

def get(request, field, searchstring):

    if not require_login_or_key(request):
        return redirect('/')

    try:
        if field == 'name':
            member = Member.objects.get(name=searchstring)
        elif field == 'username':
            member = Member.objects.get(username=searchstring)
        elif field == 'ssn':
            member = Member.objects.get(ssn=searchstring)
    except Member.DoesNotExist as e:
        return json_error('No such member')

    response_data = {
        'success': True,
        'data': member_to_dict(member)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')

def add(request):

    if not require_login_or_key(request):
        return redirect('/')

    ssn = request.GET.get('ssn')
    username = request.GET.get('username')
    name = request.GET.get('name')
    email = request.GET.get('email')
    added = request.GET.get('added', '')
    groups = request.GET.getlist('group', [])
    print groups, "list"

    member = Member()
    member.ssn = ssn
    member.username = username
    member.name = name
    member.email = email
    member.added = added

    try:
        member.save()
        member = Member.objects.get(id=member.id)
        for group in groups:
            member.groups.add(Group.objects.get(techname=group))        
    except IntegrityError as e:
        return json_error(e)

    response_data = {
        'success': True,
        'data': member_to_dict(member)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')


