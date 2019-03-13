# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render

@login_required
def user_management(request):

    users = User.objects.order_by('-is_active', '-is_superuser')

    ctx = {
        'users': users,
    }
    return render(request, 'core/user_management.html', ctx)
