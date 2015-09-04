from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^list/', 'message.views.list', name='list'),
    url(r'^add/$', 'message.views.add', name='add'),
    url(r'^edit/(?P<message_id>\d+)/$', 'message.views.edit', name='edit'),
    url(r'^delete/(?P<message_id>\d+)/$', 'message.views.delete', name='delete'),
    url(r'^view/(?P<message_id>\d+)/$', 'message.views.view', name='view'),

    url(r'^interactive/list/$', 'message.views.interactive_list', name='interactive_list'),
    url(r'^interactive/edit/(?P<interactive_type>.+)/$', 'message.views.interactive_edit', name='interactive_edit'),
    url(r'^interactive/view/(?P<interactive_type>.+)/$', 'message.views.interactive_view', name='interactive_view'),

    url(r'^mailcommand/(?P<interactive_type>.+)/(?P<link>.+)/(?P<random_string>.+)/$', 'message.views.mailcommand', name='mailcommand'),
)
