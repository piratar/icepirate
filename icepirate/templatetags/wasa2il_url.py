from django import template
from django.conf import settings

import icepirate.utils

register = template.Library()

@register.filter(needs_autoescape=True)
def wasa2il_url(member, autoescape=None):
    return icepirate.utils.wasa2il_url(member)
