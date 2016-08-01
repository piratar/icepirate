import datetime
import pytz
import sys
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from icepirate.utils import lookup_national_registry
from icepirate.utils import merge_national_registry_info
from locationcode.models import LocationCode
from member.models import Member


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--lack-muni', action='store_true', dest='lack-muni')
        parser.add_argument('--dump-ssns', action='store_true', dest='dump-ssns')
        parser.add_argument('--update-as-json', action='store_true', dest='update-as-json')
        parser.add_argument('--update-db', action='store_true', dest='update-db')
        parser.add_argument('--intersect', action='store_true', dest='intersect')
        parser.add_argument('--ssn', nargs='*', dest='ssn')
        parser.add_argument('--loc-code', nargs='*', dest='loc-code')
        parser.add_argument('--refresh', nargs='*', dest='refresh', type=str)
        for arg in ('url', 'password', 'username', 'xml_namespace'):
            parser.add_argument('--%s' % arg, nargs='*', type=str, dest=arg)

    def handle(self, *args, **options):

        # These arguments let us override the Django settings from
        # the CLI - necessary while we don't want to enable the new
        # gateway completely.
        for arg in ('url', 'password', 'username', 'xml_namespace'):
            if options.get(arg):
                settings.NATIONAL_REGISTRY[arg] = options.get(arg)[0]

        # Each of the selection arguments creates a set of users...

        # These are the users that lack a legal municipality code.
        user_sets = []
        if options.get('lack-muni', False):
            user_sets.append(
               set(Member.objects.filter(legal_municipality_code=None)) |
               set(Member.objects.filter(legal_municipality_code='')))

        # These are users whose SSN we have specified manually.
        ssn = []
        for ssns in (options.get('ssn') or []):
            ssn.extend([s.strip().replace('-', '') for s in ssns.split(',')])
        if ssn:
            user_sets.append(
                set(Member.objects.filter(ssn__in=ssn)))

        # These are users in a particular location
        locs = []
        for loc in (options.get('loc-code') or []):
            locs.extend([lc.strip() for lc in loc.split(',')])
        if locs:
            users = []
            for lc in locs:
                users.extend(LocationCode.objects.get(
                   location_code=lc).get_members())
            user_sets.append(set(users))

        # These are users whose last legal-lookup happened before a deadline.
        # An example of usage: --refresh=$(date +%s '6 months ago')
        if options.get('refresh'):
            deadline_set = set()
            for deadline in options.get('refresh'):
                when = datetime.datetime.utcfromtimestamp(int(deadline))
                when = when.replace(tzinfo=pytz.utc)
                deadline_set |= (
                   set(Member.objects.filter(legal_lookup_timing__lt=when)))
            user_sets.append(deadline_set)

        # The specified user sets are combined, either by intersecting them
        # (constraint AND constraint AND ...) or combining (OR).
        users = user_sets.pop(0)
        for uset in user_sets:
            if options.get('intersect', False):
                users &= uset
            else:
                users |= uset

        if not users:
            sys.stderr.write('No users, nothing to do.\n')

        else:
            sys.stderr.write('Processing %d users...\n' % len(users))
            if options.get('dump-ssns'):
                print '\n'.join(user.ssn for user in sorted(users))

            dump = []
            if options.get('update-db') or options.get('update-as-json'):
                for user in users:
                    nr_info = lookup_national_registry(user.ssn)

                    if options.get('update-db'):
                        sys.stderr.write('Updating %s in DB\n' % user.ssn)
                        now = timezone.now()
                        merge_national_registry_info(user, nr_info, now)
                        user.save()

                    if options.get('update-as-json'):
                        dump.append(nr_info)

            if dump:
                json.dump(dump, sys.stdout)
