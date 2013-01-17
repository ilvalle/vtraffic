# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = ' '.join(
    word.capitalize() for word in request.application.split('_'))
#response.subtitle = T('customize me!')

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Paolo Valleri'
response.meta.description = 'Demo to show some figures'
response.meta.generator = 'Web2py Web Framework'

response.google_analytics_id = "UA-34703572-1"

response.menu = [
	(A('INTEGREEN', _href="http://integreen-life.bz.it/", _class="brand"), False, None),
	(T('Add station'), False, URL('default', 'add_station'), []),
	(T('Add log'), False, URL('default', 'add_log'), []),
	(T('Origin/Destination'), request.function == 'origin_destination' , URL('default', 'origin_destination')),
	(T('Compare'), request.function == 'compare' , URL('default', 'compare'), []),
]
