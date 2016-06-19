import sys
import csv

from django.core.management.base import BaseCommand

from member.models import Member

class Command(BaseCommand):

    KNOWN_FIELDS = ('skip',
                    'ssn',
                    'name',
                    'username',
                    'email',
                    'phone',
                    'legal_name',
                    'legal_address',
                    'legal_zip_code',
                    'legal_municipality_code',
                    'legal_lookup_timing')

    def add_arguments(self, parser):
        parser.add_argument('csv_file', nargs=1, type=str)
        parser.add_argument('fields', nargs='*', type=str)

    def handle(self, *args, **options):

        # Verify that we understand all the fields
        update_fields = options['fields']
        for field in update_fields:
            if field not in self.KNOWN_FIELDS:
                raise ValueError('Unknown field: %s' % field)

        # Load the CSV data
        updates = {}
        with open(options['csv_file'][0], 'r') as fd:
            for row in csv.reader(fd):
                assert(len(row[0]) == 10)
                assert(int(row[0]) > 0)
                assert(len(row) == len(update_fields) + 1)
                updates[row[0]] = row[1:]

        # Iterate through all members and update them if necessary
        updated = []
        members = Member.objects.all()
        sys.stderr.write('Updating %d of %d members ...'
                         % (len(updates), len(members)))
        for member in members:
            update = updates.get(member.ssn)
            if update:
                del updates[member.ssn]
                sys.stderr.write('.')

                changed = False
                for i, field in enumerate(update_fields):
                    if field == 'skip':
                        pass
                    elif field in self.KNOWN_FIELDS:
                        member.__setattr__(field, update[i])
                        changed = True
                    else:
                        raise ValueError('Unknown field: %s' % field)

                    # TODO: Add support for bulk updates of group membership

                if changed:
                    updated.append(member.ssn)
                    member.save()

        sys.stderr.write('\n')
        sys.stderr.write('Updated %d members:\n\t%s\n' % (len(updated), updated))
        if updates:
            sys.stderr.write('No members found for updates:\n\t%s\n' % (
                '\n\t'.join('%s: %s' % (k, updates[k])
                            for k in sorted(updates.keys()))))
