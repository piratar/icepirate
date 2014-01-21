from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from group.models import Group
from member.models import Member
from member.forms import MemberForm

from member import kennitala

@login_required
def list(request):

    members = Member.objects.all().order_by('added')

    return render_to_response('member/list.html', { 'members': members })

@login_required
def add(request):

    if request.method == 'POST':
        form = MemberForm(request.POST)

        if form.is_valid():
            member = form.save()
            return HttpResponseRedirect('/member/view/%s' % member.kennitala)

    else:
        form = MemberForm()

    return render_to_response('member/add.html', { 'form': form }, context_instance=RequestContext(request))

@login_required
def edit(request, kennitala):

    member = get_object_or_404(Member, kennitala=kennitala)

    if request.method == 'POST':
        member.groups = request.POST.getlist('groups')
        form = MemberForm(request.POST, instance=member)

        if form.is_valid():
            member = form.save()
            return HttpResponseRedirect('/member/view/%s/' % kennitala)

    else:
        form = MemberForm(instance=member)

    return render_to_response('member/edit.html', { 'form': form, 'member': member }, context_instance=RequestContext(request))

@login_required
def delete(request, kennitala):

    member = get_object_or_404(Member, kennitala=kennitala)

    if request.method == 'POST':
        member.delete()
        return HttpResponseRedirect('/member/list/')

    return render_to_response('member/delete.html', { 'member': member }, context_instance=RequestContext(request))

@login_required
def view(request, kennitala):

    member = get_object_or_404(Member, kennitala=kennitala)

    return render_to_response('member/view.html', { 'member': member }, context_instance=RequestContext(request))

