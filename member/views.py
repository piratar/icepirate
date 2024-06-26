from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

from core.loggers import log_action
from core.jaapi import PersonNotFoundException

from member.models import Member
from member.models import MemberGroup
from member.models import MemberStat
from member.models import Subscriber
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
            log_action(
                user=request.user,
                action='member_search',
                action_details=search,
                affected_members=found_members
            )

    else:
        form = SearchForm()

    # Get subscriber count. Subscribers are unsearchable and not listed in the
    # interface, as there is no known reason for administrators to see them.
    subscriber_count = Subscriber.objects.filter(email_verified=True).count()

    context = {
        'form': form,
        'found_members': found_members,
        'member_count': members.count(),
        'have_username_count': members.filter(username__isnull=False).count(),
        'subscriber_count': subscriber_count,
        'membergroups': membergroups,
        'membergroup_techname': membergroup_techname,
        'membergroup': membergroup,
    }
    return render(request, 'member/list.html', context)


@login_required
def add(request):

    if request.method == 'POST':
        form = MemberForm(request.user, request.POST)

        if form.is_valid():
            member = form.save()

            # Log the action.
            log_action(
                user=request.user,
                action='member_add',
                affected_members=[member]
            )

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
            log_action(
                user=request.user,
                action='member_edit',
                affected_members=[member]
            )

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
        log_action(
            user=request.user,
            action='member_delete',
            affected_members=[member]
        )

        member.delete()

        return HttpResponseRedirect('/member/list/')

    return render(request, 'member/delete.html', { 'member': member })

@login_required
def view(request, ssn):

    try:
        member = Member.objects.safe(request.user).select_related('legal_municipality').get(ssn=ssn)
    except Member.DoesNotExist:
        raise Http404

    # Log the action.
    log_action(
        user=request.user,
        action='member_view',
        affected_members=[member]
    )

    ctx = {
        'member': member,
        'cost': '%d %s' % (
            settings.NATIONAL_REGISTRY_LOOKUP_COST,
            settings.NATIONAL_REGISTRY_LOOKUP_CURRENCY,
        ),
    }
    return render(request, 'member/view.html', ctx)


@login_required
def national_registry_lookup(request, ssn):
    try:
        member = Member.objects.safe(request.user).get(ssn=ssn)
    except Member.DoesNotExist:
        raise Http404

    # Log the action.
    log_action(
        user=request.user,
        action='member_national_registry_lookup',
        affected_members=[member]
    )

    try:
        member.update_from_national_registry()
        member.save()
    except PersonNotFoundException:
        ctx = {
            'errors': [_('National registry lookup failed')],
            'member': member,
            'cost': '%d %s' % (
                settings.NATIONAL_REGISTRY_LOOKUP_COST,
                settings.NATIONAL_REGISTRY_LOOKUP_CURRENCY,
            ),
        }
        return render(request, 'member/view.html', ctx)


    return HttpResponseRedirect('/member/view/%s/' % member.ssn)


@login_required
def member_stats(request):

    #############################
    # General member statistics #
    #############################

    current_member_count = Member.objects.all().count()
    member_stats = MemberStat.objects.all()

    ################################
    # National registry statistics #
    ################################
    with_municipality = Member.objects.exclude(legal_municipality=None).count()
    without_municipality = current_member_count - with_municipality

    cost_individual = settings.NATIONAL_REGISTRY_LOOKUP_COST
    cost_all = current_member_count * cost_individual
    cost_without_municipality = without_municipality * cost_individual

    # We are not going to treat these as MemberGroup items but rather as
    # constituencies. They are MemberGroup items that have municipalities as a
    # condition.
    constituencies = MemberGroup.objects.annotate(
        muni_count=Count('condition_municipalities')
    ).filter(
        muni_count__gt=0
    )

    # This can be slow. Only viewed seldomly by very few people.
    for constituency in constituencies:
        munis = constituency.condition_municipalities.all()
        constituency.resident_count = Member.objects.filter(legal_municipality__in=munis).count()

    ctx = {
        'current_member_count': current_member_count,
        'member_stats': member_stats,

        'with_municipality': with_municipality,
        'without_municipality': without_municipality,

        'currency': settings.NATIONAL_REGISTRY_LOOKUP_CURRENCY,
        'cost_individual': cost_individual,
        'cost_all': cost_all,
        'cost_without_municipality': cost_without_municipality,

        'constituencies': constituencies,
    }
    return render(request, 'member/stats.html', ctx)


@login_required
def membergroup_list(request):

    membergroups = MemberGroup.objects.safe(request.user).all()

    return render(request, 'group/list.html', { 'membergroups': membergroups})


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

