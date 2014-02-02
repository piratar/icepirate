from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(needs_autoescape=True)
def printadmin(user, autoescape=None):
    try:
        name = user.username
        fullname = user.get_full_name()
        if fullname != '':
            name = fullname
        if user.email != '':
            return mark_safe('<a href="mailto:%s">%s</a>' % (user.email, name))
        else:
            return mark_safe(name)
    except:
        return user

