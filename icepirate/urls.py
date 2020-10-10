from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.contrib.auth.views import LogoutView
from django.urls import path

from member import views as member_views

from message.views import short_url_redirect

from core import views as core_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),

    url(r'^accounts/logout/$', LogoutView.as_view(), { 'next_page': '/accounts/login' }),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^login/$', RedirectView.as_view(url='/accounts/login/')),
    url(r'^user-management/$', core_views.user_management, name='user_management'),

    url(r'^member/', include('member.urls')),
    url(r'^group/list/', member_views.membergroup_list, name='membergroup_list'),
    url(r'^group/add/', member_views.membergroup_add, name='membergroup_add'),
    url(r'^group/edit/(?P<techname>[^/]+)', member_views.membergroup_edit, name='membergroup_edit'),
    url(r'^group/delete/(?P<techname>[^/]+)', member_views.membergroup_delete, name='membergroup_delete'),
    url(r'^group/view/(?P<techname>[^/]+)', member_views.membergroup_view, name='membergroup_view'),

    url(r'^message/', include('message.urls')),
    url(r'^r/(?P<code>[^/]+)/?$', short_url_redirect),

    url(r'^$', RedirectView.as_view(url='/accounts/login/')),
]

if settings.DEBUG:
    if 'debug_toolbar.apps.DebugToolbarConfig' in settings.INSTALLED_APPS:
        try:
            import debug_toolbar
            urlpatterns += [
                url(r'^__debug__/', include(debug_toolbar.urls)),
            ]
        except:
            pass
