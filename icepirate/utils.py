# -*- coding: utf-8 -*-
import hashlib
import json
import os

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils.translation import ugettext as _

import re

def validate_ssn(ssn):
    # Must be precisely 10 numerical digits
    if len(ssn) != 10 or not ssn.isdigit():
        return False

    tempsum = int(ssn[0]) * 3
    tempsum = tempsum + int(ssn[1]) * 2
    tempsum = tempsum + int(ssn[2]) * 7
    tempsum = tempsum + int(ssn[3]) * 6
    tempsum = tempsum + int(ssn[4]) * 5
    tempsum = tempsum + int(ssn[5]) * 4
    tempsum = tempsum + int(ssn[6]) * 3
    tempsum = tempsum + int(ssn[7]) * 2

    checksum = 11 - (tempsum % 11)

    return checksum == int(ssn[8]) or (checksum == 11 and int(ssn[8]) == 0)

def techify(input_string):
    result = input_string.strip().lower()

    table = {
        ord(u' '): u'-',
        ord(u'á'): u'a',
        ord(u'ð'): u'd',
        ord(u'é'): u'e',
        ord(u'í'): u'i',
        ord(u'ó'): u'o',
        ord(u'ú'): u'u',
        ord(u'ý'): u'y',
        ord(u'þ'): u'th',
        ord(u'æ'): u'ae',
        ord(u'ö'): u'o',
    }

    result = result.translate(table)

    result = re.sub('[^\-a-z0-9+]', '', result)

    return result

def quick_mail(to, subject, body, from_email=settings.DEFAULT_FROM_EMAIL, subject_prefix=settings.EMAIL_SUBJECT_PREFIX):

    real_subject = subject
    if subject_prefix:
        real_subject = u'[%s] %s' % (subject_prefix, real_subject)


    send_mail(
        real_subject,
        body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to,],
        fail_silently=False
    )

def generate_random_string():
    return hashlib.sha1(os.urandom(128)).hexdigest()

def json_error(exception):
    response_data = {
        'success': False,
        'error': exception.__str__()
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')


