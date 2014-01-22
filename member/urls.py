from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

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
	url(r'^list/(?P<group_techname>.*)', 'member.views.list', name='list'),
    url(r'^add/', 'member.views.add', name='add'),
    url(r'^edit/(?P<kennitala>[^/]+)', 'member.views.edit', name='edit'),
    url(r'^delete/(?P<kennitala>[^/]+)', 'member.views.delete', name='delete'),
    url(r'^view/(?P<kennitala>[^/]+)', 'member.views.view', name='view'),

    # CSV
    url(r'^csv/list/(?P<group_techname>.*)', 'member.views_csv.list', name='csv_list'),

    # API pages (JSON)
	url(r'^api/list/', 'member.views_api.list', name='api_list'),
	url(r'^api/filter/(?P<field>.*)/(?P<searchstring>.+)', 'member.views_api.filter', name='api_filter'),
	url(r'^api/get/(?P<field>.*)/(?P<searchstring>.+)', 'member.views_api.get', name='api_get'),

)
