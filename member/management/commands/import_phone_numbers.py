from django.core.management.base import BaseCommand
from member.models import Member

# WARNING! This is a quick and dirty way to import phone numbers in a
# particular format that will almost certainly never be used again. It is
# retained here in case we ever have to do the same thing again, but then
# this script will almost certainly need to be updated to accommodate the
# new format.
#
# Note also that the data that this script inputs should NEVER, EVER be
# committed to the git repository.

class Command(BaseCommand):

    def handle(self, *args, **options):
        lines = []
        with open('data/phone-numbers.csv', 'r', encoding='iso-8859-1') as f:
            lines = f.read().split('\n')
        
        for i, line in enumerate(lines):
            # First line is the header and we're not interested in empty lines.
            if i == 0 or line == '':
                continue

            # Get fields from CSV.
            (ssn, name, email, phone, garbage, more_garbage) = line.split(',')

            # Not interested in phone numbers that don't exist.
            if phone == '':
                continue

            # Attempt to sanity-check and fix phone number.
            if len(phone) != 7:
                phone = phone.replace(' ', '')
            if len(phone) != 7:
                raise Exception('Phone number should be 7 digits: %s (line %d)' % (ssn, i))

            # Attempt to sanity-check and fix SSN.
            if len(ssn) == 9:
                ssn = '0%s' % ssn
            if len(ssn) != 10:
                raise Exception('SSN should be 10 digits: %s (line %d)' % (ssn, i))
            
            # Update user if necessary.
            member = Member.objects.get(ssn=ssn)
            if member.phone != phone:
                member.phone = phone
                member.save()
