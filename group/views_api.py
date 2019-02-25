import json

from django.conf import settings
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from member.models import MemberGroup

def require_login_or_key(request):
    return request.user.is_authenticated() or request.GET.get('json_api_key') == settings.JSON_API_KEY

def groups_to_dict(groups):

	result = []
	for group in groups:
		result.append({
			'name': group.name,
			'techname': group.techname,
			'email': group.email
		})
	return result

def list(request):
    if not require_login_or_key(request):
        return redirect('/')

    groups = MemberGroup.objects.all().order_by('name')

    response_data = {
        'success': True,
        'data': groups_to_dict(groups)
    }

    return HttpResponse(json.dumps(response_data), content_type='application/json')
