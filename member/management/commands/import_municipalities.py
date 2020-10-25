# About this script
# =================
# Written on 2020-10-25.
#
# Municipalities of Iceland were retrieved from URL:
# 
#     https://www.samband.is/wp-content/uploads/2020/06/sveitfax_20200618.xls
#
# which was found at:
#
#     https://www.samband.is/sveitarfelogin/

# The Excel file was opened with LibreOffice 6.4.6.2 and saved again as an
# identically named CSV file (with only the file ending being different) with
# the following export settings:
#
# - Character set: Unicode (UTF-8)
# - Field delimeter: ,
# - String delimeter: "
# -[x] Save cell content as shown
# -[ ] Save cell formulas instead of calculated values
# -[x] Quote all text cells
# -[ ] Fixed column width
#
# This script takes the resulting CSV file and updates the `Municipality`
# table accordingly.
#
# If we're lucky, changes to municipalities in the future will be published in
# the exact same way, making it easy to update data on our end.
from django.core.management.base import BaseCommand
from member.models import Municipality

FILE_INPUT_CSV = 'data/source-data/sveitfax_20200618.csv'

class Command(BaseCommand):

    def handle(self, *args, **options):

        with open(FILE_INPUT_CSV, 'r') as f:
            lines = f.read().split('\n')

        municipalities = {}
        for i, line in enumerate(lines):
            # Account for possible double-quotes and meaningless whitespace.
            values = [v.strip('"').strip() for v in line.split(',')]

            # We are only interested in municipality-lines, whose first value
            # is a four-digit numerical code for the municipality.
            if len(values[0]) == 4:
                # We record the email and website basically for kicks. There is more
                # data available that might be worth using later.
                municipalities[values[0]] = {
                    'name': values[1],
                    'email': values[12],
                    # Assuming HTTPS because people should notice and fix it
                    # if any of these websites still have their traffic
                    # unencrypted.
                    'website': 'https://%s' % values[13] if values[13] else '',
                }

        # Figure out which municipalities need to be added or deleted.
        imported_codes = set([code for code in municipalities])
        current_codes = set(Municipality.objects.values_list('code', flat=True))
        to_be_added = imported_codes - current_codes
        to_be_deleted = current_codes - imported_codes

        # Add codes that don't already exist.
        for code in municipalities:
            if code in to_be_added:
                Municipality(code=code, name=municipalities[code]['name']).save()

        # Delete codes that should not exist.
        Municipality.objects.filter(code__in=to_be_deleted).delete()
