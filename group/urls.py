from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^list/', 'group.views.list', name='list'),
    url(r'^add/', 'group.views.add', name='add'),
    url(r'^edit/(?P<techname>[^/]+)', 'group.views.edit', name='edit'),
    url(r'^delete/(?P<techname>[^/]+)', 'group.views.delete', name='delete'),
    url(r'^view/(?P<techname>[^/]+)', 'group.views.view', name='view'),

)
