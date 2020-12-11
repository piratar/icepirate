from django.conf.urls import include
from django.conf.urls import url
from django.urls import path

from message import views
from message import views_api

urlpatterns = [
    url(r'^list/', views.list, name='list'),
    url(r'^add/$', views.add, name='add'),
    url(r'^edit/(?P<message_id>\d+)/$', views.edit, name='edit'),
    url(r'^delete/(?P<message_id>\d+)/$', views.delete, name='delete'),
    url(r'^view/(?P<message_id>\d+)/$', views.view, name='view'),

    url(r'^interactive/list/$', views.interactive_list, name='interactive_list'),
    url(r'^interactive/edit/(?P<interactive_type>.+)/$', views.interactive_edit, name='interactive_edit'),
    url(r'^interactive/view/(?P<interactive_type>.+)/$', views.interactive_view, name='interactive_view'),

    url(r'^mailcommand/(?P<interactive_type>.+)/(?P<link>.+)/(?P<random_string>.+)/$', views.mailcommand, name='mailcommand'),

    path('api/testsend/<int:message_id>/', views_api.testsend, name='api_testsend'),
]
