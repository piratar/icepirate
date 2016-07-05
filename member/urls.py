from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.http import urlencode

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'icepirate.views.home', name='home'),
    # url(r'^icepirate/', include('icepirate.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    # ------------------------------------------------------------------#

    # General stuff.
    url(r'^list/in/(?P<location_code>[^/]*)', 'member.views.list'),
    url(r'^list/(?P<group_techname>.+)/(?P<combined>combined)', 'member.views.list', name='list'),
    url(r'^list/(?P<group_techname>.*)', 'member.views.list', name='list'),
    url(r'^add/', 'member.views.add', name='add'),
    url(r'^edit/(?P<ssn>[^/]+)', 'member.views.edit', name='edit'),
    url(r'^delete/(?P<ssn>[^/]+)', 'member.views.delete', name='delete'),
    url(r'^view/(?P<ssn>[^/]+)', 'member.views.view', name='view'),
    url(r'^count/location/(?P<grep>[^/]*)', 'member.views.location_count', name='location_count'),
    url(r'^count/(?P<grep>[^/]*)', 'member.views.count', name='count'),

    # Verification
    url(r'^verify-start/$', lambda r: redirect(settings.AUTH_URL)),
    url(r'^verify/', 'member.views.verify', name='verify'),

    # CSV
    url(r'^csv/list/in/(?P<location_code>[^/]*)', 'member.views_csv.list'),
    url(r'^csv/list/(?P<group_techname>[^/]*)/(?P<combined>[^/]+)', 'member.views_csv.list'),
    url(r'^csv/list/(?P<group_techname>[^/]*)', 'member.views_csv.list', name='csv_list'),

    # API pages (JSON)
    url(r'^api/list/', 'member.views_api.list', name='api_list'),
    url(r'^api/filter/(?P<field>.*)/(?P<searchstring>.+)', 'member.views_api.filter', name='api_filter'),
    url(r'^api/get/(?P<field>.*)/(?P<searchstring>.+)', 'member.views_api.get', name='api_get'),
    url(r'^api/add/$', 'member.views_api.add', name='api_add'),
    url(r'^api/count/$', 'member.views_api.count', name='api_count'),

)
