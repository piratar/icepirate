import datetime
import pytz

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from member.models import MemberGroup
from member.forms import MemberGroupForm

from icepirate.utils import techify

@login_required
def list(request):

    membergroups = MemberGroup.objects.all().order_by('name')

    return render(request, 'group/list.html', { 'membergroups': membergroups})

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
    for membergroup in MemberGroup.objects.all().order_by('name'):
        joined = []
        for i, date in enumerate(dates[1:]):
            joined.append(membergroup.get_members().filter(
                added__gte=dates[i], added__lt=date).count())
        stats.append({
            'group': membergroup,
            'joined': joined,
            'total': membergroup.get_members().count()})

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
        return render(request, 'group/stats.html', { 'dates': dates, 'stats': stats })

@login_required
def add(request):

    if request.method == 'POST':
        form = MemberGroupForm(request.POST)

        if form.is_valid():
            form.instance.techname = techify(form.cleaned_data['name'])
            membergroup = form.save()
            return HttpResponseRedirect('/group/view/%s' % membergroup.techname)

    else:
        form = MemberGroupForm()

    return render(request, 'group/add.html', { 'form': form })

@login_required
def edit(request, techname):

    membergroup = get_object_or_404(MemberGroup, techname=techname)

    if request.method == 'POST':
        form = MemberGroupForm(request.POST, instance=membergroup)

        if form.is_valid():
            form.instance.techname = techify(form.cleaned_data['name'])
            membergroup = form.save()
            return HttpResponseRedirect('/group/view/%s/' % membergroup.techname)

    else:
        form = MemberGroupForm(instance=membergroup)

    return render(request, 'group/edit.html', { 'form': form, 'membergroup': membergroup })

@login_required
def delete(request, techname):

    membergroup = get_object_or_404(MemberGroup, techname=techname)

    if request.method == 'POST':
        membergroup.delete()
        return HttpResponseRedirect('/group/list/')

    return render(request, 'group/delete.html', { 'membergroup': membergroup })

@login_required
def view(request, techname):
    membergroup = get_object_or_404(MemberGroup, techname=techname)

    return render(request, 'group/view.html', { 'membergroup': membergroup })

