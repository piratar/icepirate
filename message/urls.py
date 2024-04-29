from django.urls import path, re_path

from message import views
from message import views_api

urlpatterns = [
    path('list/', views.list, name='list'),
    path('add/', views.add, name='add'),
    path('edit/<int:message_id>/', views.edit, name='edit'),
    path('delete/<int:message_id>/', views.delete, name='delete'),
    path('view/<int:message_id>/', views.view, name='view'),

    path('interactive/list/', views.interactive_list, name='interactive_list'),
    re_path(r'^interactive/edit/(?P<interactive_type>.+)/$', views.interactive_edit, name='interactive_edit'),
    re_path(r'^interactive/view/(?P<interactive_type>.+)/$', views.interactive_view, name='interactive_view'),

    re_path(r'^mailcommand-complete/(?P<interactive_type>.+)/(?P<link>.+)/(?P<random_string>.+)/$', views.mailcommand_complete, name='mailcommand_complete'),
    re_path(r'^mailcommand/(?P<interactive_type>.+)/(?P<link>.+)/(?P<random_string>.+)/$', views.mailcommand, name='mailcommand'),

    path('api/testsend/<int:message_id>/', views_api.testsend, name='api_testsend'),
]
