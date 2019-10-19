import pytz

from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.shortcuts import redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from core.models import ActionEvent

from member.models import Member
from member.models import MemberGroup
from locationcode.models import LocationCode
from member.forms import MemberForm
from member.forms import MemberGroupForm
from member.forms import SearchForm

from member import ssn

from icepirate.utils import techify

@login_required
def list(request, membergroup_techname=None):

    membergroups = MemberGroup.objects.safe(request.user).all()

    if membergroup_techname:
        try:
            membergroup = membergroups.get(techname=membergroup_techname)
        except MemberGroup.DoesNotExist:
            raise Http404

        members = Member.objects.safe(request.user).filter(membergroups=membergroup)
    else:
        membergroup = None
        members = Member.objects.safe(request.user).all()

    # Handle search.
    found_members = None
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search = form.cleaned_data['search_string']

            found_members = members

            for part in search.split(' '):
                found_members = found_members.filter(
                    Q(ssn__icontains=part)
                    | Q(name__icontains=part)
                    | Q(username__icontains=part)
                    | Q(email__icontains=part)
                    | Q(phone__icontains=part)
                    | Q(added__icontains=part)
                    #| Q(legal_name__icontains=part)
                    #| Q(legal_zone__icontains=part)
                )

            if settings.MAX_MEMBERS_SHOWN > -1 and found_members.count() > settings.MAX_MEMBERS_SHOWN:
                found_members = []
                form.add_error(None, _(
                    'Please narrow the search down to %d results or less.' % settings.MAX_MEMBERS_SHOWN
                ))

            # Log the action.
            ActionEvent(
                user=request.user,
                action='member_search',
                action_details=search,
                affected_members=found_members
            ).save()

    else:
        form = SearchForm()

    context = {
        'form': form,
        'found_members': found_members,
        'member_count': members.count(),
        'have_username_count': members.filter(username__isnull=False).count(),
        'membergroups': membergroups,
        'membergroup_techname': membergroup_techname,
        'membergroup': membergroup,
    }
    return render(request, 'member/list.html', context)


'''
# Disabled because this mechanism doesn't give correct numbers. This way of
# counting members assumes that no one has ever left the organization. The
# proper way to create this statistic is to collect numbers every month and
# write them down somewhere.
@login_required
def count(request, grep=None):
    members_by_month = Member.objects.all().extra(select={'month': 'extract( month from added )','year':'extract(year from added)'}).values('month', 'year')
    results = {}
    for entry in members_by_month:
        added = str(entry['year'])+'-'+str(entry['month']).zfill(2)
        if (not grep) or grep in added:
            if added in results:
                results[added] += 1
            else:
                results[added] = 1
    context = {
        'grouping': 'Year-Month',
        'data': sorted(results.iteritems())
    }
    return render(request, 'member/count.html', context)
'''

@login_required
def add(request):

    if request.method == 'POST':
        form = MemberForm(request.user, request.POST)

        if form.is_valid():
            member = form.save()

            # Log the action.
            ActionEvent(
                user=request.user,
                action='member_add',
                affected_members=[member]
            ).save()

            return HttpResponseRedirect('/member/view/%s' % member.ssn)

    else:
        form = MemberForm(request.user)

    return render(request, 'member/add.html', { 'form': form })

@login_required
def edit(request, ssn):

    try:
        member = Member.objects.safe(request.user).get(ssn=ssn)
    except Member.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = MemberForm(request.user, request.POST, instance=member)

        if form.is_valid():
            member = form.save()

            # Log the action.
            ActionEvent(
                user=request.user,
                action='member_edit',
                affected_members=[member]
            ).save()

            return HttpResponseRedirect('/member/view/%s/' % member.ssn)

    else:
        form = MemberForm(request.user, instance=member)

    return render(request, 'member/edit.html', { 'form': form, 'member': member })

@login_required
def delete(request, ssn):

    if not request.user.is_superuser:
        raise Http404

    member = get_object_or_404(Member, ssn=ssn)

    if request.method == 'POST':
        member_id = member.id

        # Log the action.
        ActionEvent(
            user=request.user,
            action='member_delete',
            affected_members=[member]
        ).save()

        member.delete()

        return HttpResponseRedirect('/member/list/')

    return render(request, 'member/delete.html', { 'member': member })

@login_required
def view(request, ssn):

    try:
        member = Member.objects.safe(request.user).get(ssn=ssn)
    except Member.DoesNotExist:
        raise Http404

    # Log the action.
    ActionEvent(
        user=request.user,
        action='member_view',
        affected_members=[member]
    ).save()

    return render(request, 'member/view.html', { 'member': member })


@login_required
def membergroup_list(request):

    membergroups = MemberGroup.objects.safe(request.user).all()

    return render(request, 'group/list.html', { 'membergroups': membergroups})

@login_required
def membergroup_stats(request, as_csv=False):
    from member.models import Member

    # This finds the most recent "end of week" date
    week = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0)
    week = week - timedelta(days=week.weekday())

    # Calculate our date ranges.
    # There are 27 slots, which gives 26 ranges in total.
    dates = [(week - timedelta(weeks=n))
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
def membergroup_add(request):

    if not request.user.is_superuser:
        raise Http404

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
def membergroup_edit(request, techname):

    if not request.user.is_superuser:
        raise Http404

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
def membergroup_delete(request, techname):

    if not request.user.is_superuser:
        raise Http404

    membergroup = get_object_or_404(MemberGroup, techname=techname)

    if request.method == 'POST':
        membergroup.delete()
        return HttpResponseRedirect('/group/list/')

    return render(request, 'group/delete.html', { 'membergroup': membergroup })

@login_required
def membergroup_view(request, techname):

    try:
        membergroup = MemberGroup.objects.safe(request.user).get(techname=techname)
    except Member.DoesNotExist:
        raise Http404

    return render(request, 'group/view.html', { 'membergroup': membergroup })

