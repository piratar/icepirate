from django.conf.urls import include
from django.conf.urls import url

from group import views
from group import views_api

urlpatterns = [
    url(r'^list/', views.list, name='list'),
    url(r'^stats/(?P<as_csv>csv)/', views.stats, name='stats'),
    url(r'^stats/', views.stats, name='stats'),
    url(r'^add/', views.add, name='add'),
    url(r'^edit/(?P<techname>[^/]+)', views.edit, name='edit'),
    url(r'^delete/(?P<techname>[^/]+)', views.delete, name='delete'),
    url(r'^view/(?P<techname>[^/]+)', views.view, name='view'),

    #api
    url(r'^api/list/', views_api.list, name='list'),
]
