from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.urls import path

from member import views
from member import views_api
from member import views_csv

urlpatterns = [
    # Examples:
    # url(r'^$', 'icepirate.views.home', name='home'),
    # url(r'^icepirate/', include('icepirate.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    # ------------------------------------------------------------------#

    # General stuff.
    url(r'^list/(?P<membergroup_techname>.*)', views.list, name='list'),
    url(r'^add/', views.add, name='add'),
    url(r'^edit/(?P<ssn>[^/]+)', views.edit, name='edit'),
    url(r'^delete/(?P<ssn>[^/]+)', views.delete, name='delete'),
    url(r'^view/(?P<ssn>[^/]+)', views.view, name='view'),
    path('national-registry-lookup/<str:ssn>/', views.national_registry_lookup, name='national_registry_lookup'),

    # Verification
    # Commented because not in use, seems incomplete and isn't documented.
    #url(r'^verify-start/$', lambda r: redirect(settings.AUTH_URL)),
    #url(r'^verify/', views.verify, name='verify'),

    url(r'^csv/list/(?P<group_techname>[^/]*)', views_csv.list, name='csv_list'),

    # API pages (JSON)
    url(r'^api/get/(?P<field>.*)/(?P<searchstring>.+)/', views_api.get, name='api_get'),
    url(r'^api/add/$', views_api.add, name='api_add'),
    url(r'^api/update/ssn/(?P<ssn>[^/]+)/$', views_api.update, name='api_update'),
    url(r'^api/count/$', views_api.count, name='api_count'),
    path('api/subscribe-to-mailinglist/', views_api.subscribe_to_mailinglist),
]
