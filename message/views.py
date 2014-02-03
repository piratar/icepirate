from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from message.forms import MessageForm
from message.models import Message

@login_required
def list(request):

    return render_to_response('message/list.html')

@login_required
def add(request):

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            form.instance.author = request.user
            form.instance.ready_to_send = request.POST.get('ready_to_send', False)
            message = form.save()
            return HttpResponseRedirect('/message/view/%d' % message.id)

    else:
        form = MessageForm()

    return render_to_response('message/add.html', { 'form': form }, context_instance=RequestContext(request))

@login_required
def edit(request, message_id):

    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST' and not message.sending_started:
        form = MessageForm(request.POST, instance=message)

        if form.is_valid():
            form.instance.author = request.user
            form.instance.ready_to_send = request.POST.get('ready_to_send', False)
            message = form.save()
            return HttpResponseRedirect('/message/view/%d/' % message.id)

    else:
        form = MessageForm(instance=message)

    return render_to_response('message/edit.html', { 'form': form, 'message': message }, context_instance=RequestContext(request))

@login_required
def delete(request, message_id):

    message = get_object_or_404(Message, id=message_id)

    if request.method == 'POST' and not message.sending_started:
        message.delete()
        return HttpResponseRedirect('/message/list/')

    return render_to_response('message/delete.html', { 'message': message }, context_instance=RequestContext(request))


@login_required
def list(request):
    messages = Message.objects.select_related('groups').all()

    return render_to_response('message/list.html', { 'messages': messages })

@login_required
def view(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    return render_to_response('message/view.html', { 'message': message }, context_instance=RequestContext(request))

