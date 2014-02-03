from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^list/', 'message.views.list', name='list'),
    url(r'^add/$', 'message.views.add', name='add'),
    url(r'^edit/(?P<message_id>\d+)/$', 'message.views.edit', name='edit'),
    url(r'^delete/(?P<message_id>\d+)/$', 'message.views.delete', name='delete'),
    url(r'^view/(?P<message_id>\d+)/$', 'message.views.view', name='view'),
)
