from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.contrib.auth.views import logout

from message.views import short_url_redirect

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/logout/$', logout, { 'next_page': '/accounts/login' }),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^login/$', RedirectView.as_view(url='/accounts/login/')),

    url(r'^member/', include('member.urls')),
    url(r'^group/', include('group.urls')),

    url(r'^message/', include('message.urls')),
    url(r'^r/(?P<code>[^/]+)/?$', short_url_redirect),

    url(r'^$', RedirectView.as_view(url='/accounts/login/')),
]
