from datetime import datetime

from django.conf import settings
from django.http import Http404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import RequestContext

from member.models import Member

from message.forms import InteractiveMessageForm
from message.forms import MessageForm
from message.models import InteractiveMessage
from message.models import Message, ShortURL

@login_required
def add(request):

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            form.instance.author = request.user
            form.instance.ready_to_send = len(request.POST.get('ready_to_send', '')) > 0
            message = form.save()
            return HttpResponseRedirect('/message/view/%d' % message.id)

    else:
        form = MessageForm()

    return render(request, 'message/add.html', { 'form': form })

@login_required
def edit(request, message_id):

    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST' and not message.sending_started:
        form = MessageForm(request.POST, instance=message)

        if form.is_valid():
            form.instance.author = request.user
            form.instance.ready_to_send = len(request.POST.get('ready_to_send', '')) > 0
            message = form.save()
            return HttpResponseRedirect('/message/view/%d/' % message.id)

    else:
        form = MessageForm(instance=message)

    return render(request, 'message/edit.html', { 'form': form, 'message': message })

@login_required
def delete(request, message_id):

    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST' and not message.sending_started:
        message.delete()
        return HttpResponseRedirect('/message/list/')

    return render(request, 'message/delete.html', { 'message': message })


@login_required
def list(request):
    messages = Message.objects.select_related('author').prefetch_related('membergroups', 'locations').all()

    return render(request, 'message/list.html', { 'messages': messages })

@login_required
def view(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    return render(request, 'message/view.html', { 'message': message })

@login_required
def interactive_list(request):
    interactive_messages = InteractiveMessage.objects.filter(active=True)

    display_struct = {}
    for m in interactive_messages:
        if not display_struct.has_key(m.interactive_type):
            display_struct[m.interactive_type] = {}

        display_struct[m.interactive_type]['active_message'] = m

    for i_type, i_display in InteractiveMessage.INTERACTIVE_TYPES:
        if not display_struct.has_key(i_type):
            display_struct[i_type] = {}

        display_struct[i_type]['display'] = i_display

    return render(request, 'message/interactive_list.html', { 'display_struct': display_struct })

@login_required
def interactive_edit(request, interactive_type):

    if interactive_type not in dict(InteractiveMessage.INTERACTIVE_TYPES):
        raise Exception('Interactive type "%s" not recognized' % interactive_type)

    try:
        interactive_message = InteractiveMessage.objects.get(interactive_type=interactive_type, active=True)
    except InteractiveMessage.DoesNotExist:
        interactive_message = InteractiveMessage(interactive_type=interactive_type)

    if request.method == 'POST':
        form = InteractiveMessageForm(request.POST, instance=interactive_message)

        if form.is_valid():
            # If the previous message has already been sent to a user, we make a new one and make the old one inactive
            if form.instance.pk != None and form.instance.deliveries.count() > 0:
                # Inactivate the previous message
                InteractiveMessage.objects.filter(pk=form.instance.pk).update(active=False)

                # Make a new copy
                form.instance.added = datetime.now()
                form.instance.pk = None

            form.instance.interactive_type = interactive_type
            form.instance.author = request.user
            interactive_message = form.save()
            return HttpResponseRedirect('/message/interactive/view/%s/' % interactive_type)

    else:
        form = InteractiveMessageForm(instance=interactive_message)

    if form.instance.interactive_type in InteractiveMessage.INTERACTIVE_TYPES_DETAILS:
        interactive_type = form.instance.interactive_type # Only to fit the next line
        form.fields['body'].help_text = InteractiveMessage.INTERACTIVE_TYPES_DETAILS[interactive_type]['description']

    ctx = {
        'form': form,
        'interactive_message': interactive_message,
    }
    return render(request, 'message/interactive_edit.html', ctx)

@login_required
def interactive_view(request, interactive_type):
    interactive_message = get_object_or_404(InteractiveMessage, interactive_type=interactive_type, active=True)

    # This example code is only to make the URLs seem more realistic when they are being viewed. It is not a secret.
    example_code = '0z7vW2lqAAnd1VoZp091Voa'

    if InteractiveMessage.INTERACTIVE_TYPES_DETAILS.has_key(interactive_message.interactive_type):
        links = InteractiveMessage.INTERACTIVE_TYPES_DETAILS[interactive_message.interactive_type]['links']
        for link in links:
            replacement = 'https://example.com/member/mailcommand/%s/%s/%s' % (
                interactive_message.interactive_type,
                link,
                example_code
            )
            interactive_message.body = interactive_message.body.replace('{{%s}}' % link, replacement)

    return render(request, 'message/interactive_view.html', { 'interactive_message': interactive_message })


def short_url_redirect(request, code=None):
    try:
        return HttpResponseRedirect(
            ShortURL.objects.get(code=code, added__gte=ShortURL.Expired()
            ).url)
    except ShortURL.DoesNotExist:
        ShortURL.DeleteExpired()
        return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)


def mailcommand(request, interactive_type, link, random_string):
    if interactive_type == 'registration_received':
        if link == 'confirm':
            try:
                member = Member.objects.get(temporary_web_id=random_string)
            except Member.DoesNotExist:
                return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)

            member.email_verified = True
            member.save()

            return render(request, 'message/mailcommand.html', {
                'interactive_type': interactive_type,
                'link': link,
                'redirect_countdown': 10,
                'redirect_url': settings.ORGANIZATION_MAIN_URL,
                'member': member,
            })
        elif link == 'reject':
            try:
                member = Member.objects.get(temporary_web_id=random_string)
            except Member.DoesNotExist:
                return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)

            member.delete()

            return render(request, 'message/mailcommand.html', {
                'interactive_type': interactive_type,
                'link': link,
                'redirect_countdown': 30,
                'redirect_url': settings.ORGANIZATION_MAIN_URL,
                'organization_email': settings.ORGANIZATION_EMAIL,
            })
        else:
            return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)
    elif interactive_type == 'reject_email_messages':
        if link == 'reject_link':
            try:
                member = Member.objects.get(temporary_web_id=random_string)
            except Member.DoesNotExist:
                return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)

            member.email_wanted = False
            member.save()

            return render(request, 'message/mailcommand.html', {
                'interactive_type': interactive_type,
                'link': link,
                'redirect_countdown': 30,
                'redirect_url': settings.ORGANIZATION_MAIN_URL,
                'member': member,
                'organization_email': settings.ORGANIZATION_EMAIL,
            })
    else:
        return HttpResponseRedirect(settings.ORGANIZATION_MAIN_URL)

