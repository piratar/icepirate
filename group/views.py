from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from group.models import Group
from group.forms import GroupForm

from icepirate.utils import techify

@login_required
def list(request):

    groups = Group.objects.all().order_by('name')

    return render_to_response('group/list.html', { 'groups': groups})

@login_required
def add(request):

    if request.method == 'POST':
        form = GroupForm(request.POST)

        if form.is_valid():
            form.instance.techname = techify(form.cleaned_data['name'])
            group = form.save()
            return HttpResponseRedirect('/group/view/%s' % group.techname)

    else:
        form = GroupForm()

    return render_to_response('group/add.html', { 'form': form }, context_instance=RequestContext(request))

@login_required
def edit(request, techname):

    group = get_object_or_404(Group, techname=techname)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)

        if form.is_valid():
            form.instance.techname = techify(form.cleaned_data['name'])
            group = form.save()
            return HttpResponseRedirect('/group/view/%s/' % group.techname)

    else:
        form = GroupForm(instance=group)

    return render_to_response('group/edit.html', { 'form': form, 'group': group }, context_instance=RequestContext(request))

@login_required
def delete(request, techname):

    group = get_object_or_404(Group, techname=techname)

    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect('/group/list/')

    return render_to_response('group/delete.html', { 'group': group }, context_instance=RequestContext(request))

@login_required
def view(request, techname):
    group = get_object_or_404(Group, techname=techname)

    return render_to_response('group/view.html', { 'group': group }, context_instance=RequestContext(request))

