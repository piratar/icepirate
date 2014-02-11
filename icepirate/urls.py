from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	# Examples:
	# url(r'^$', 'icepirate.views.home', name='home'),
	# url(r'^icepirate/', include('icepirate.foo.urls')),

	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', { 'next_page': '/accounts/login' }),
    url(r'^accounts/', include('registration.urls')),

	url(r'^member/', include('member.urls')),
    url(r'^group/', include('group.urls')),
    url(r'^message/', include('message.urls')),

    url(r'^$', RedirectView.as_view(url='/member/verify-start/')),
)
