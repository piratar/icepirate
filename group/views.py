import datetime
import pytz

from django.http import HttpResponseRedirect, HttpResponse
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
def stats(request, as_csv=False):
    from member.models import Member

    # This finds the most recent "end of week" date
    week = datetime.datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0)
    week = week - datetime.timedelta(days=week.weekday())

    # Calculate our date ranges.
    # There are 27 slots, which gives 26 ranges in total.
    dates = [(week - datetime.timedelta(weeks=n))
             for n in reversed(range(0, 27))]

    # Grab per-group stats
    stats = []
    for group in Group.objects.all().order_by('name'):
        joined = []
        for i, date in enumerate(dates[1:]):
            joined.append(group.get_members().filter(
                added__gte=dates[i], added__lt=date).count())
        stats.append({
            'group': group,
            'joined': joined,
            'total': group.get_members().count()})

    # Grab totals (not everyone joins a group)
    joined = []
    for i, date in enumerate(dates[1:]):
        joined.append(Member.objects.filter(
            added__gte=dates[i], added__lt=date).count())
    stats.append({
        'joined': joined,
        'total': Member.objects.count()})

    if as_csv:
        lines = ['#"Group","%s","Total"' % '","'.join(
                 unicode(d) for d in dates[1:])]
        for stat in stats:
            lines.append('"%s"' % '","'.join(
                [unicode(stat.get('group', 'TOTAL'))] +
                ['%s' % j for j in stat['joined']] +
                ['%s' % stat['total']]))

        response = HttpResponse(
            "\n".join(lines), content_type='text/csv; charset: utf-8')
        response['Content-Disposition'] = 'attachment; filename="stats.csv"'
        return response
    else:
        return render_to_response('group/stats.html', {
            'dates': dates,
            'stats': stats})

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

