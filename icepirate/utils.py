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

def quick_mail(to, subject, body,
        from_email=None,
        subject_prefix=settings.EMAIL_SUBJECT_PREFIX,
        html_body=None):

    real_subject = subject
    if subject_prefix:
        real_subject = u'[%s] %s' % (subject_prefix, real_subject)

    return send_mail(
        real_subject,
        body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to,],
        fail_silently=False,
        html_message=html_body)

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

def get_http_response(web_url, data=None, quit_on_failure=False):
    retry_count = 2
    success = False
    while not success and retry_count > 0:
        try:
            response = urlopen(web_url, data=data, timeout=5)
            success = True
        except HTTPError:
            break
        except IOError as e:
            sys.stderr.write('Error, will retry: %s\n' % e)
            retry_count -= 1
            time.sleep(1)

    if success:
        return response
    else:
        sys.stderr.write('Error: Failed retrieving URL: %s\n' % web_url)
        if quit_on_failure:
            quit(1)
        raise

def lookup_national_registry_lt(ssn):
    nr_url = settings.NATIONAL_REGISTRY['url']
    nr_username = settings.NATIONAL_REGISTRY['username']
    nr_password = settings.NATIONAL_REGISTRY['password']
    nr_xml_namespace = settings.NATIONAL_REGISTRY['xml_namespace']

    nr_data = urlencode({
        'username': nr_username,
        'password': nr_password,
        'regno': ssn,
        'requesterregno': '',
    }).encode('utf-8')

    response = get_http_response(nr_url, data=nr_data, quit_on_failure=True)
    content = response.read()
    #sys.stderr.write('%s => %s\n' % (ssn, content.decode('utf-8')))

    # Parse the XML. Yes, it's painful to look at, and it should be, it's XML.
    xmldoc = etree.fromstring(content)
    result = {
        'is_individual': xmldoc.find('.//ns:IsIndividual', namespaces={'ns': nr_xml_namespace}).text == 'true',
        'is_current': xmldoc.find('.//ns:IsCurrent', namespaces={'ns': nr_xml_namespace}).text == 'true',
        'is_valid': xmldoc.find('.//ns:IsValid', namespaces={'ns': nr_xml_namespace}).text == 'true',
    }

    if result['is_valid']:
        result.update({
            'name': xmldoc.find('.//ns:FullName', namespaces={'ns': nr_xml_namespace}).text,
            'legal_address': xmldoc.find('.//ns:LegalAddress', namespaces={'ns': nr_xml_namespace}).text,
            'legal_zip_code': xmldoc.find('.//ns:LegalZipCode', namespaces={'ns': nr_xml_namespace}).text,
            'legal_zone': xmldoc.find('.//ns:LegalZone', namespaces={'ns': nr_xml_namespace}).text,
            'legal_municipality_code': None
        })

    return result

def lookup_national_registry_ferli(ssn):
    nr_url = settings.NATIONAL_REGISTRY['url']
    nr_password = settings.NATIONAL_REGISTRY['password']
    nr_xml_namespace = settings.NATIONAL_REGISTRY['xml_namespace']

    nr_data = urlencode({
        'str_Ktala': unicode(ssn).replace('-', ''),
        'str_Password': nr_password
    })

    try:
        response = get_http_response(nr_url, data=nr_data, quit_on_failure=False)
        content = response.read()
        #sys.stderr.write('%s => %s\n' % (ssn, content.decode('utf-8')))
        found_in_nr = True
    except HTTPError:
        found_in_nr = False
    except IOError as e:
        quit(1)

    # Parse the XML. Yes, it's painful to look at, and it should be, it's XML.
    nsp = {'ns': nr_xml_namespace}
    if found_in_nr:
        xmldoc = etree.fromstring(content)
        tegrec = xmldoc.find('//ns:TegRec', namespaces=nsp)
        kynkodi = xmldoc.find('//ns:KynKodi', namespaces=nsp)
        retkod = xmldoc.find('//ns:Retkod', namespaces=nsp)
    else:
        tegrec = kynkodi = retkod = None

    result = {
        'is_individual': (kynkodi is not None) and (kynkodi.text.strip()) and True or False,
        'is_current': (retkod is not None and '0' == retkod.text),
        'is_valid': (retkod is not None and '0' == retkod.text),
    }

    if result['is_valid']:
        result.update({
            'name': xmldoc.find('//ns:Nafn', namespaces=nsp).text,
            'legal_address': xmldoc.find('//ns:Heimili', namespaces=nsp).text,
            'legal_zip_code': xmldoc.find('//ns:Postnr', namespaces=nsp).text,
            'legal_zone': xmldoc.find('//ns:Sveitarfelag', namespaces=nsp).text,
            'legal_municipality_code': xmldoc.find('//ns:SveitarfNum', namespaces=nsp).text,
        })

    return result

def lookup_national_registry(ssn):
    namespace = settings.NATIONAL_REGISTRY['xml_namespace']

    # FIXME: This seems a bit silly.
    if 'ws.lt.is' in namespace:
        return lookup_national_registry_lt(ssn)

    elif 'xml.ferli.is' in namespace:
        return lookup_national_registry_ferli(ssn)

    raise NotImplementedError('Unknown XML namespace, halp')


def merge_national_registry_info(member, nr_info, now):
    try:
        assert(nr_info.get('name') and nr_info.get('is_individual'))
    except:
        sys.stderr.write('Failed to update %s (%s) with %s\n' % (
            force_bytes(unicode(member)),
            force_bytes(member.ssn),
            force_bytes('%s' % nr_info)))
        raise

    member.legal_name = nr_info['name']

    if nr_info.get('legal_address'):
        member.legal_address = nr_info['legal_address']
    if nr_info.get('legal_zip_code'):
        member.legal_zip_code = nr_info['legal_zip_code']
    if nr_info.get('legal_zone'):
        member.legal_zone = nr_info['legal_zone']
    if nr_info.get('legal_municipality_code'):
        member.legal_municipality_code = nr_info['legal_municipality_code']

    member.legal_lookup_timing = now
    return member


def wasa2il_url(member, data=None, verified=False, shorten=False):
    url = settings.WASA2IL_HOME_URL
    data = copy.copy(data or {})
    try:
        if member.username:
            url = settings.WASA2IL_LOGIN_URL
            data['username'] = member.username
        elif member.email:
            url = settings.WASA2IL_REGISTRATION_URL
            data['email'] = member.email
            if verified or member.email_verified:
                 data['email_sig'] = member.email_sig()
    except:
        pass

    url = '%s?%s' % (url, urlencode(data))
    if shorten:
        from message.models import ShortURL
        return str(ShortURL(url=url).save())
    else:
        return url
