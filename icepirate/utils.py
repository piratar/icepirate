# -*- coding: utf-8 -*-
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
