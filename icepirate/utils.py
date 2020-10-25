# -*- coding: utf-8 -*-
import copy
import hashlib
import json
import os
import sys
import time
from lxml import etree
from io import StringIO
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from django.conf import settings
from django.http import HttpResponse
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext as _
from django_mdmail import send_mail

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

def quick_mail(to, subject, body, from_email=None, subject_prefix=settings.EMAIL_SUBJECT_PREFIX):

    real_subject = subject
    if subject_prefix:
        real_subject = u'[%s] %s' % (subject_prefix, real_subject)

    return send_mail(
        real_subject,
        body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to,],
        fail_silently=False
    )

def generate_random_string():
    some_random = hashlib.sha1(os.urandom(128)).hexdigest()[:40]

    # Technically, this could repeat every 16 years or so. But it's
    # so unlikely that we just don't really care. The SHA1 above
    # really should be enough on its own, this is all overkill.
    #
    # Of course, we ARE assuming time never stands still or goes
    # backwards... but even if we're wrong about that: SHA1 ftw.
    #
    now = int(time.time() * 0x7f01f) & 0xffffffffffff
    return (
        '%x%x%s' % (os.getpid(), now, some_random)
        ).replace('.', '')[:40]

def json_error(exception):
    response_data = {
        'success': False,
        'error': exception.__str__()
    }
    return HttpResponse(json.dumps(response_data), content_type='application/json')
