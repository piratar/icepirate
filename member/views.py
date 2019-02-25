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

from member.models import Member
from member.models import MemberGroup
from locationcode.models import LocationCode
from member.forms import MemberForm
from member.forms import MemberGroupForm
from member.forms import SearchForm

from member import ssn

from icepirate.saml import authenticate
from icepirate.utils import techify

@login_required
def list(request, group_techname=None, location_code=None, combined=False):

    group = None
    if group_techname:
        group = MemberGroup.objects.get(techname=group_techname)
        if combined:
            members = group.get_members()
            if members.count() == group.members.count():
                combined = False
        else:
            members = group.members.all()
        location_code = None

    elif location_code:
        location_code = LocationCode.objects.get(location_code=location_code)
        members = location_code.get_members()
        combined = False

    else:
        members = Member.objects.all()
        combined = False

    membergroups = MemberGroup.objects.all()
    location_codes = LocationCode.objects.all()

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
                found_members = None
                form.add_error(None, _(
                    'Please narrow the search down to %d results or less.' % settings.MAX_MEMBERS_SHOWN
                ))

    else:
        form = SearchForm()

    context = {
        'form': form,
        'found_members': found_members,
        'member_count': members.count(),
        'have_username_count': members.filter(username__isnull=False).count(),
        'membergroups': membergroups,
        'location_codes': location_codes,
        'group_techname': group_techname,
        'group': group,
        'location_code': location_code,
        'combined': combined
    }
    return render(request, 'member/list.html', context)

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

@login_required
def location_count(request, grep=None):
    results = {}
    for loc in LocationCode.objects.all():
        if (not grep) or grep in unicode(loc):
            results[unicode(loc)] = loc.get_members().count()
    context = {
        'grouping': 'LocationCode',
        'data': sorted(results.iteritems())
    }
    return render(request, 'member/count.html', context)

@login_required
def add(request):

    if request.method == 'POST':
        form = MemberForm(request.POST)

        if form.is_valid():
            member = form.save()
            return HttpResponseRedirect('/member/view/%s' % member.ssn)

    else:
        form = MemberForm()

    return render(request, 'member/add.html', { 'form': form })

@login_required
def edit(request, ssn):

    member = get_object_or_404(Member, ssn=ssn)

    if request.method == 'POST':
        member.membergroups = request.POST.getlist('membergroups')
        form = MemberForm(request.POST, instance=member)

        if form.is_valid():
            member = form.save()
            return HttpResponseRedirect('/member/view/%s/' % member.ssn)

    else:
        form = MemberForm(instance=member)

    return render(request, 'member/edit.html', { 'form': form, 'member': member })

@login_required
def delete(request, ssn):

    member = get_object_or_404(Member, ssn=ssn)

    if request.method == 'POST':
        member.delete()
        return HttpResponseRedirect('/member/list/')

    return render(request, 'member/delete.html', { 'member': member })

@login_required
def view(request, ssn):

    member = get_object_or_404(Member, ssn=ssn)

    return render(request, 'member/view.html', { 'member': member })

def verify(request):

    member = None

    ssn = request.session.get('ssn', None)
    if ssn:
        member = Member.objects.get(ssn=ssn)

    if member is None:
        auth = authenticate(request, settings.AUTH_URL)
        try:
            member = Member.objects.get(ssn=auth['ssn'])
            member.verified = True
            member.auth_token = request.GET['token']
            member.auth_timing = datetime.now()
            member.save()

            request.session['ssn'] = member.ssn
            return redirect('/member/verify/')
        except:
            pass

    return render(request, 'member/verify.html', { 'member': member, })

@login_required
def membergroup_list(request):

    membergroups = MemberGroup.objects.all().order_by('name')

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

    membergroup = get_object_or_404(MemberGroup, techname=techname)

    if request.method == 'POST':
        membergroup.delete()
        return HttpResponseRedirect('/group/list/')

    return render(request, 'group/delete.html', { 'membergroup': membergroup })

@login_required
def membergroup_view(request, techname):
    membergroup = get_object_or_404(MemberGroup, techname=techname)

    return render(request, 'group/view.html', { 'membergroup': membergroup })

