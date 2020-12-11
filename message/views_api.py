from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from jsonview.decorators import json_view
from member.models import Subscriber
from message.models import Message


@login_required
@json_view
def testsend(request, message_id):

    # Get and validate email address.
    to_email = request.POST.get('to_email', None)
    try:
        validate_email(to_email)
    except ValidationError:
        raise Exception('Field to_email must be valid email address (%s)' % to_email)

    # Get message.
    message = get_object_or_404(Message, id=message_id)

    # Create a fake recipient (doesn't get saved to database) to simulate it
    # being sent to one.
    recipient = Subscriber(
        email=to_email,
        temporary_web_id='some-random-string'
    )

    # Send the test email.
    success = message.send(recipient, testsend=True)

    ctx = {
        'success': success,
    }
    return ctx
