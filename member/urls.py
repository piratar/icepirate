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

    # General member stuff.
    url(r'^member/list/(?P<membergroup_techname>.*)', views.list, name='list'),
    url(r'^member/add/', views.add, name='add'),
    url(r'^member/edit/(?P<ssn>[^/]+)', views.edit, name='edit'),
    url(r'^member/delete/(?P<ssn>[^/]+)', views.delete, name='delete'),
    url(r'^member/view/(?P<ssn>[^/]+)', views.view, name='view'),
    path('member/national-registry-lookup/<str:ssn>/', views.national_registry_lookup, name='national_registry_lookup'),
    path('member/stats/', views.member_stats, name='member_stats'),

    # MemberGroup stuff.
    url(r'^group/list/', views.membergroup_list, name='membergroup_list'),
    url(r'^group/add/', views.membergroup_add, name='membergroup_add'),
    url(r'^group/edit/(?P<techname>[^/]+)', views.membergroup_edit, name='membergroup_edit'),
    url(r'^group/delete/(?P<techname>[^/]+)', views.membergroup_delete, name='membergroup_delete'),
    url(r'^group/view/(?P<techname>[^/]+)', views.membergroup_view, name='membergroup_view'),

    # Verification
    # Commented because not in use, seems incomplete and isn't documented.
    #url(r'^verify-start/$', lambda r: redirect(settings.AUTH_URL)),
    #url(r'^verify/', views.verify, name='verify'),

    url(r'^member/csv/list/(?P<group_techname>[^/]*)', views_csv.list, name='csv_list'),

    # API pages (JSON)
    url(r'^member/api/get/(?P<field>.*)/(?P<searchstring>.+)/', views_api.get, name='api_get'),
    url(r'^member/api/add/$', views_api.add, name='api_add'),
    url(r'^member/api/update/ssn/(?P<ssn>[^/]+)/$', views_api.update, name='api_update'),
    url(r'^member/api/count/$', views_api.count, name='api_count'),
    path('member/api/add-to-membergroup/<str:ssn>/', views_api.add_to_membergroup),
    path('member/api/subscribe-to-mailinglist/', views_api.subscribe_to_mailinglist),
]
