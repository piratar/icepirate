import json
import sys
import time
import traceback

from django.conf import settings
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from icepirate.utils import json_error

from member.models import Member
from member.models import MemberGroup


def require_login_or_key(request):
    return request.user.is_authenticated() or request.POST.get('json_api_key') == settings.JSON_API_KEY


def access_denied():
    return json_error('Access denied')


def member_to_dict(member):

    result = {
        'ssn': member.ssn,
        'name': member.name,
        'username': member.username,
        'email': member.email,
        'email_wanted': member.email_wanted,
        'phone': member.phone,
        'added': member.added.strftime('%Y-%m-%d %H:%M:%S'),
        'groups': []
    }

    for key, val in (
            ('legal_name', member.legal_name),
            ('legal_address', member.legal_address),
            ('legal_zip_code', member.legal_zip_code),
            ('legal_municipality_code', member.legal_municipality_code)):
        if val:
            result[key] = val

    all_groups = member.get_groups()
    main_groups = member.groups.all()

    result['groups'] = dict([(g.techname, g.name) for g in all_groups])
    result['main_groups'] = dict([(g.techname, g.name) for g in main_groups])
    result['auto_groups'] = dict([(g.techname, g.name) for g in (set(all_groups) - set(main_groups))])

    return result


@csrf_exempt
def get(request, field, searchstring):

    if not require_login_or_key(request):
        return access_denied()

    try:
        if field == 'name':
            member = Member.objects.get(name=searchstring)
        elif field == 'username':
            member = Member.objects.get(username=searchstring)
        elif field == 'ssn':
            member = Member.objects.get(ssn=searchstring)
        else:
            return json_error('No such member')
    except Member.DoesNotExist as e:
        return json_error('No such member')

    response_data = {
        'success': True,
        'data': member_to_dict(member)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')


@csrf_exempt
def update(request, ssn):

    if not require_login_or_key(request):
        return access_denied()

    input_vars = request.POST
    if settings.DEBUG and request.method == 'GET':
        input_vars = request.GET

    updated_fields = []

    # Get user.
    try:
        member = Member.objects.get(ssn=ssn)
    except Member.DoesNotExist:
        return json_error('No such member')

    # Update member with data from the remote end.
    try:
        username = input_vars.get('username', '')
        email = input_vars.get('email', '')
        if 'email_wanted' in input_vars:
            email_wanted = str(input_vars.get('email_wanted', '')).lower() == 'true'
        else:
            # No change.
            email_wanted = None

        if username and member.username != username:
            member.username = username
            updated_fields.append('username')

        if email and member.email != email:
            # We trust client to have verified the e-mail.
            member.email = email
            member.email_verified = True
            updated_fields.append('email')

        if email_wanted is not None and member.email_wanted != email_wanted:
            member.email_wanted = email_wanted
            updated_fields.append('email_wanted')

        if len(updated_fields) > 0:
            member.save()

    except Exception as e:
        raise IcePirateException(e)

    response_data = {
        'success': True,
        'updated_fields': updated_fields,
        'data': member_to_dict(member),
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')


@csrf_exempt
def add(request):

    if not require_login_or_key(request):
        return access_denied()

    input_vars = request.POST
    if settings.DEBUG and request.method == 'GET':
        input_vars = request.GET

    required_fields = ['ssn', 'username', 'name', 'email']
    if not all([(field in input_vars) for field in required_fields]):
        return json_error('The following fields are required: %s' % required_fields)

    ssn = input_vars.get('ssn')
    username = input_vars.get('username')
    name = input_vars.get('name')
    email = input_vars.get('email')
    email_wanted = str(input_vars.get('email_wanted', '')).lower() == 'true'
    added = input_vars.get('added', timezone.now())
    groups = input_vars.getlist('group', [])

    # Make sure that the member doesn't already exist.
    if Member.objects.filter(Q(ssn=ssn) | Q(username=username)).count() != 0:
        return json_error('Member already exists')

    member = Member()
    member.ssn = ssn
    member.username = username
    member.name = name
    member.email = email
    member.email_wanted = email_wanted
    member.added = added

    try:
        member.save()
        member.refresh_from_db()
        for group in groups:
            try:
                member.groups.add(MemberGroup.objects.get(techname=group))
            except MemberGroup.DoesNotExist:
                # Nothing to see here. Move along.
                pass
    except Exception as e:
        raise IcePirateException(e)

    response_data = {
        'success': True,
        'data': member_to_dict(member)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')


def count(request):
    if not require_login_or_key(request):
        return access_denied()
        
    members_by_month = Member.objects.all().extra(select={'month': 'extract( month from added )','year':'extract(year from added)'}).values('month', 'year')
    results = {}
    for entry in members_by_month:
        added = str(entry['year'])+'-'+str(entry['month'])
        if added in results:
            results[added] += 1
        else:
            results[added] = 1
    return HttpResponse(json.dumps(results), content_type='application/json')
