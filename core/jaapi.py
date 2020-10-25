# Documentation: http://gagnatorg.ja.is/docs/skra/v1/
# Usage: https://api.ja.is/usage/[key]/
import json
import requests

from django.conf import settings

BASE_URL = 'https://api.ja.is/skra/v1/'

def parse_json(url):
    response = requests.get(url, headers={ 'Authorization': settings.NATIONAL_REGISTRY_KEY })
    return json.loads(response.text)

def get_person(kt):
    url = '%s%s/%s' % (BASE_URL, 'people', kt)
    return parse_json(url)
