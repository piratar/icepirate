from django.urls import path
from django.urls import re_path

from member import views, views_api, views_csv

urlpatterns = [
    # Uncomment the admin/doc line below to enable admin documentation:
    # path('admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # path('admin/', admin.site.urls),

    # General member stuff
    re_path(r'^member/list/(?P<membergroup_techname>.*)', views.list, name='list'),
    path('member/add/', views.add, name='add'),
    re_path(r'^member/edit/(?P<ssn>[^/]+)', views.edit, name='edit'),
    re_path(r'^member/delete/(?P<ssn>[^/]+)', views.delete, name='delete'),
    re_path(r'^member/view/(?P<ssn>[^/]+)', views.view, name='view'),
    path('member/national-registry-lookup/<str:ssn>/', views.national_registry_lookup, name='national_registry_lookup'),
    path('member/stats/', views.member_stats, name='member_stats'),

    # MemberGroup stuff
    path('group/list/', views.membergroup_list, name='membergroup_list'),
    path('group/add/', views.membergroup_add, name='membergroup_add'),
    re_path(r'^group/edit/(?P<techname>[^/]+)', views.membergroup_edit, name='membergroup_edit'),
    re_path(r'^group/delete/(?P<techname>[^/]+)', views.membergroup_delete, name='membergroup_delete'),
    re_path(r'^group/view/(?P<techname>[^/]+)', views.membergroup_view, name='membergroup_view'),

    re_path(r'^member/csv/list/(?P<group_techname>[^/]*)', views_csv.list, name='csv_list'),

    # API pages (JSON)
    re_path(r'^member/api/get/(?P<field>.*)/(?P<searchstring>.+)/', views_api.get, name='api_get'),
    path('member/api/add/', views_api.add, name='api_add'),
    re_path(r'^member/api/update/ssn/(?P<ssn>[^/]+)/$', views_api.update, name='api_update'),
    path('member/api/count/', views_api.count, name='api_count'),
    path('member/api/add-to-membergroup/<str:ssn>/', views_api.add_to_membergroup),
    path('member/api/subscribe-to-mailinglist/', views_api.subscribe_to_mailinglist),
]
