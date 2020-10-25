#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script plan:

if SSN checksum is OK
    if member in local database
        if new groups requested
            register member to requested groups

        if new email
            notify admins and task them with investigation
            (do nothing else)

        if email is unchanged
            check for changes in consent to emails being sent
            if consent is different from database
                note or revoke consent

    else
        if SSN is in national registry
            if names do not match (first and last)
                notify admins
                (continue)

            send confirmation email

            (confirmation mechanism not contained in script, see message/urls.py)
            if confirmed
                register to local database
                redirect user to confirmation page
            else if rejected
                delete registration from database
                redirect user to rejection page
        else
            do nothing
else
    do nothing (because JavaScript should have stopped it already)

'''

from django.core.management.base import BaseCommand

import imaplib
import email
import json
import locale
import os
import pytz
from core import jaapi
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from email.header import decode_header
from sys import stderr
from sys import stdout
from datetime import datetime
from datetime import timedelta
from dateutil import parser as dateparser

from icepirate.utils import quick_mail
from icepirate.utils import generate_random_string
from icepirate.utils import techify
from icepirate.utils import validate_ssn
from member.models import Member
from member.models import MemberGroup
from message.models import InteractiveMessage


class Command(BaseCommand):

    character_translation_table = {
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


    def handle(self, *args, **options):

        # Observe Ctrl-C
        try:
            stdout.write('Processing started at %s\n' % timezone.now())

            # First we make sure that the registration_received email (interactive message)
            # has been configured in the web app.
            try:
                InteractiveMessage.objects.get(interactive_type='registration_received')
            except InteractiveMessage.DoesNotExist:
                raise Exception('Interactive message "Registration received" must be configured before running this script.')

            registration_requests = self.get_registration_requests()
            for reg in registration_requests:
                stdout.write('Processing registration (%s, %s, %s)\n' % (reg['ssn'], reg['name'], reg['email']))

                try:
                    if self.check_if_valid_ssn(reg):
                        existing_member = self.is_already_member(reg)
                        if existing_member:
                            added_to_groups = self.process_groups(reg, existing_member)

                            emails_differ = self.check_if_emails_differ(reg)

                            if not emails_differ:
                                email_consent_changed = self.check_if_email_consent_changed(reg)
                            else:
                                email_consent_changed = False

                            if not added_to_groups and not emails_differ and not email_consent_changed:
                                stdout.write('* Registration ignored.\n')
                        else:
                            if self.check_national_registry(reg):
                                if not self.check_names(reg):
                                    if not self.recently_mailed_about(reg):
                                        self.notify_name_mismatch(reg)

                                self.register_member(reg)

                            else:
                                stdout.write('* Registration ignored.\n')

                    else:
                        stdout.write('* Registration ignored.\n')
                except Exception as e:
                    stdout.write('Error: %s\n' % e)
                    stdout.write('THERE HAS BEEN AN ERROR. Continuing with registrations.\n')

                stdout.write('\n')

        except KeyboardInterrupt:
            quit(1)
        except Exception as e:
            stderr.write('Error: %s\n' % e)


    def check_if_valid_ssn(self, reg):
        stdout.write('- Checking if SSN %s is valid...' % reg['ssn'])
        stdout.flush()

        if validate_ssn(reg['ssn']):
            stdout.write(' yes\n')

            return True
        else:
            stdout.write(' no\n')

            return False


    def check_names(self, reg):
        stdout.write('- Checking if names match ("%s" and "%s")...' % (reg['name'], reg['national']['name']))
        stdout.flush()

        input_name = reg['name']
        national_name = reg['national']['name']

        input_name = input_name.translate(self.character_translation_table)
        national_name = national_name.translate(self.character_translation_table)

        input_name_first = input_name.split(' ', 1)[0]
        input_name_last = input_name.rsplit(None, 1)[-1]

        national_name_first = national_name.split(' ', 1)[0]
        national_name_last = national_name.rsplit(None, 1)[-1]

        names_match = (
            input_name_first.lower() == national_name_first.lower()
            and input_name_last.lower() == national_name_last.lower()
        )

        if names_match:
            stdout.write(' yes\n')
        else:
            stdout.write(' no\n')

        return names_match

    def recently_mailed_about(self, reg):
        email = reg['email'].lower()
        filename = os.path.expanduser('~/recently-mailed-about.json')
        try:
            with open(filename, 'r') as fd:
                recent = json.load(fd)
        except (IOError, OSError, ValueError):
            recent = []
        if email in recent:
            return True
        else:
            recent.append(email)
            recent = recent[-100:]
            with open(filename, 'w') as fd:
                json.dump(recent, fd)
            return False

    def check_if_emails_differ(self, reg):

        member = Member.objects.get(ssn=reg['ssn'])

        stdout.write('- Checking if email addresses differ...')
        stdout.flush()
        if member.email.lower() != reg['email'].lower():
            stdout.write(' yes\n')

            if self.recently_mailed_about(reg):
                stdout.write('* Already notified admins, ignoring.\n')
            else:
                stdout.write('* Notifying admins...')
                stdout.flush()

                for admin in User.objects.filter(is_staff=True):
                    body = 'IMPORTANT!\n'
                    body += 'Someone who is already a member registered again, but they used a different email.\n'
                    body += '\n'
                    body += 'Please contact the member through both email addresses and resolve the issue.\n'
                    body += '\n'
                    body += 'Prior email address: %s\n' % member.email
                    body += 'New email address: %s\n' % reg['email']
                    body += '\n'
                    body += 'SSN: %s\n' % reg['ssn']
                    body += 'Name in registration: %s\n' % reg['name']
                    if reg['name'] != member.name:
                        body += 'Name in database: %s\n' % member.name
                    body += '\n'
                    body += 'NOTE: The member has NOT been modified in the database. Please modify manually after investigating the matter.\n'
                    quick_mail(admin.email, 'IMPORTANT! New email address in registration!', body)

                stdout.write(' done\n')

            return True
        else:
            stdout.write(' no\n')
            return False

    def check_if_email_consent_changed(self, reg):

        member = Member.objects.get(ssn=reg['ssn'])

        stdout.write('- Checking if consent for email being sent has changed...')
        stdout.flush()
        if member.email_wanted != reg['email_ok']:
            stdout.write(' yes\n')

            if reg['email_ok']:
                stdout.write('* Noting consent for email being sent...')
            else:
                stdout.write('* Revoking consent for email being sent...')
            stdout.flush()
            member.email_wanted = reg['email_ok']
            member.save()
            stdout.write(' done\n')

            return True
        else:
            stdout.write(' no\n')

            return False

    def check_national_registry(self, reg):
        stdout.write('- Checking if %s is an individual in the national registry...' % reg['ssn'])
        stdout.flush()

        national = jaapi.get_person(reg['ssn'])

        if national['type'] == 'person':
            reg['national'] = national

            stdout.write(' yes\n')

            return True
        else:
            stdout.write(' no\n')

            return False


    def is_already_member(self, reg):
        stdout.write('- Checking if registrant is already a member...')
        stdout.flush()

        member_try = Member.objects.filter(ssn=reg['ssn'])

        if member_try.count() > 0:
            stdout.write(' yes\n')

            return member_try[0]
        else:
            stdout.write(' no\n')

            return None


    def notify_name_mismatch(self, reg):
        stdout.write('* Notifying admins...')
        stdout.flush()

        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            body = 'The following registration contains a name inconsistency.\n'
            body += 'Name given by user: %s\n' % reg['name']
            body += 'Name found in national database: %s\n' % reg['national']['name']
            body += '\n'
            body += 'SSN: %s\n' % reg['ssn']
            body += '\n'
            body += 'The member was still registered as usual.\n'
            body += 'If no further action is needed, ignore this message.\n'
            body += 'Otherwise, act as considered appropriate.\n'
            quick_mail(admin.email, u'Registration name inconsistent', body)

        stdout.write(' done\n')


    # Put member in appropriate groups
    def process_groups(self, reg, member):
        added_to_groups = False
        for membergroup in MemberGroup.objects.filter(name__in=reg['member_assoc']).exclude(members=member):
            stdout.write('* Adding member to group: %s...' % membergroup.name)
            stdout.flush()
            membergroup.members.add(member)
            stdout.write(' done\n')

            added_to_groups = True

        return added_to_groups


    def register_member(self, reg):
        random_string = generate_random_string()
        while Member.objects.filter(temporary_web_id=random_string).count() > 0:
            # Preventing duplication errors
            random_string = generate_random_string()

        # Make the 'added' date timezone-aware.
        added_date = datetime.strptime(reg['date'], '%Y-%m-%d %H:%M:%S')

        # Create and configure member
        member = Member()
        member.added = pytz.timezone(settings.TIME_ZONE).localize(added_date)
        member.ssn = reg['ssn']
        member.name = reg['name']
        member.email = reg['email']
        member.email_wanted = reg['email_ok']
        member.temporary_web_id = random_string
        member.temporary_web_id_timing = timezone.now()
        member.update_from_national_registry(reg['national'])

        # Save member to database
        stdout.write('* Registering member...')
        stdout.flush()
        member.save()
        stdout.write(' done\n')

        self.process_groups(reg, member)

        # Send confirmation message
        stdout.write('* Sending confirmation email...')
        stdout.flush()
        message = InteractiveMessage.objects.get(interactive_type='registration_received')
        message.send(member.email, member.temporary_web_id)
        stdout.write(' done\n')


    # A bit of a hack to make sure we get US English formatted search date for the IMAP
    def imap_dateformat(self, input_datetime):
        old_locale = locale.setlocale(locale.LC_TIME, '')
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        result = input_datetime.strftime('%d-%b-%Y')
        locale.setlocale(locale.LC_TIME, old_locale)
        return result


    # A bit of a hack to make sure we get US English formatted search date for the IMAP
    def imap_parse_datetime(self, input_string):
        old_locale = locale.setlocale(locale.LC_TIME, '')
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        result = dateparser.parse(input_string)
        locale.setlocale(locale.LC_TIME, old_locale)
        return result


    def parse_email_content(self, email_content):
        result = {
            'ssn': '',
            'name': '',
            'member_assoc': [],
            'email_ok': False,
        }

        for line in email_content.split('\n'):
            # This part is really ugly because we receive the email in a really ugly format
            if u'Nafn:' in line:
                result['name'] = line.split(": ")[1]
            elif u'Kennitala:' in line:
                ssn = line.split(": ")[1].replace('-','').replace(' ', '')
                ssn = ''.join(c for c in ssn if c.isdigit()) # Remove non-digits
                if len(ssn) == 11 and ssn[10] == '0':
                    ssn = ssn[:10]  # Workaround for buglet in form.
                result['ssn'] = ssn
            elif u'Svæðisbundið aðildarfélag:' in line:
                member_assoc = line.split(": ")[1]
                if member_assoc != u'Ekkert':
                    result['member_assoc'].append(member_assoc)
            elif u'Ungir Píratar:' in line:
                if line.split(": ")[1] == u'Já':
                    result['member_assoc'].append(u'Ungir Píratar')
            elif u'Samþykki fyrir tölvupósti' in line:
                if line.split(": ")[1] == u'Já':
                    result['email_ok'] = True

        return result

    def get_registration_requests(self):

        # Result variable
        registrations = []

        # Make sure we have the registration configuration
        if hasattr(settings, 'NEW_REGISTRATIONS_IMAP'):
            for imap_variable in ['server', 'username', 'password', 'inbox', 'filter-to-address', 'filter-last-days']:
                if not imap_variable in settings.NEW_REGISTRATIONS_IMAP:
                    stderr.write('Error: Missing configuration for %s in NEW_REGISTRATIONS_IMAP\n' % imap_variable)
                    quit(2)
        else:
            stderr.write('Error: NEW_REGISTRATIONS_IMAP configuration missing in settings (see local_settings.py-example)\n')
            quit(2)

        # Short-hands
        imap_server = settings.NEW_REGISTRATIONS_IMAP['server']
        imap_username = settings.NEW_REGISTRATIONS_IMAP['username']
        imap_password = settings.NEW_REGISTRATIONS_IMAP['password']
        imap_inbox = settings.NEW_REGISTRATIONS_IMAP['inbox']
 
        # Configurable filters
        filter_to_address = settings.NEW_REGISTRATIONS_IMAP['filter-to-address']
        filter_since = timezone.now() - timedelta(days=settings.NEW_REGISTRATIONS_IMAP['filter-last-days'])

        stdout.write('Date filter: since %s\n' % filter_since)

        # Connect to IMAP server
        stdout.write('Connecting to server %s...' % imap_server)
        stdout.flush()
        try:
            M = imaplib.IMAP4_SSL(imap_server)
        except Exception as e:
            stdout.write(' failed: %s\n' % e)
            quit(1)
        stdout.write(' done\n')

        # Login to IMAP server
        stdout.write('Logging in...')
        stdout.flush()
        try:
            M.login(imap_username, imap_password)
        except Exception as e:
            stdout.write(' failed: %s\n' % e)
            quit(1)
        stdout.write(' done\n')

        # Select the appropriate inbox
        stdout.write('Selecting inbox...')
        stdout.flush()
        M.select(imap_inbox)
        stdout.write(' done\n')

        # Construct IMAP search filter
        search_string = u'(TO "%s" SINCE "%s")' % (
            filter_to_address,
            self.imap_dateformat(filter_since)
        )

        # Search by previously constructed filter. Emails that are marked as
        # unread will be processed, others ignored.
        stdout.write('Searching by filter...')
        stdout.flush()
        result, data = M.search(None, search_string.encode('utf-8'), '(UNSEEN)')
        stdout.write(' done\n')

        # Iterate through received email messages
        for num in data[0].split():
            stdout.write('Parsing message %s: ' % num.decode('utf-8'))
            stdout.flush()

            try:
                # Get the data in its basic form
                result, data = M.fetch(num, '(RFC822)') #fetch message number num
                raw_email = data[0][1].decode('utf-8')
                email_message = email.message_from_string(raw_email)

                if email_message.is_multipart(): # We have nothing to do with multipart messages
                    stdout.write('[multipart garbage]\n')
                    continue

                # This will contain the unprocessed information from the email
                registration = {}

                # Gather the email subject
                subject = u''
                for element in decode_header(email_message['subject']):
                    try:
                        subject = subject + ' ' + element[0].decode('utf-8')
                    except UnicodeDecodeError:
                        subject = subject + ' ' + element[0].decode('iso-8859-1')
                    except AttributeError:
                        subject = subject + ' ' + str(element[0])
                    subject = subject.strip()

                if subject[:19] != u'Skráning í Pírata: ':
                    stdout.write('\n')
                    continue

                # Get message timing
                timing = self.imap_parse_datetime(email_message['Date'][0:25])
                registration['date'] = timing.strftime("%Y-%m-%d %H:%M:%S")
                stdout.write('%s: ' % registration['date'])
                stdout.flush()

                # Get email address
                registration['email'] = email.utils.parseaddr(email_message['from'])[1]
                stdout.write('%s' % registration['email'])
                stdout.flush()

                # Parse the registration from the message
                email_content = self.parse_email_content(email_message.get_payload(decode=True).decode('utf-8'))
                registration.update(email_content)

                registrations.append(registration)

                stdout.write('\n')

            except Exception as e:
                stderr.write('Error: %s\n' % e)
                raise

        # Close connection with IMAP server
        M.close()
        M.logout()

        return registrations

