# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

import re

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

def email(to, subject, body, from_email=settings.DEFAULT_FROM_EMAIL, subject_prefix=settings.EMAIL_SUBJECT_PREFIX):

    real_subject = subject
    if subject_prefix:
        real_subject = u'[%s] %s' % (subject_prefix.decode('utf-8'), real_subject)

    send_mail(
        real_subject,
        body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to,],
        fail_silently=False
    )

