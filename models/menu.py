# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = "Vehicle traffic monitoring"
response.page_title = response.title
response.subtitle = "A free and open source approach for vehicle traffic monitoring"
#response.header_msg = " Join the presentation at FOSDEM 2013 conference! <a href='https://fosdem.org/2013/schedule/event/vehicular_traffic_estimation_through_bluetooth/'>read more</a>"

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Paolo Valleri'
response.meta.description = 'Vehicle traffic monitoring through the detection of bluetooth signals'
response.meta.generator = 'Web2py Web Framework'

response.google_analytics_id = "UA-34703572-1"
response.google_map_key = 'AIzaSyA9DDSrqpql5y89lZfnnwu6dkOiCcLf9Bk'

response.menu = [
	(SPAN('INTEGREEN'), False, 'http://www.integreen-life.bz.it', [
        (A(CAT(TAG.I(_class="icon-info-sign"), " %s" % T('Parking situation')), _href='http://parking.integreen-life.bz.it', _title="Bolzano parking situation") , False, None),
		(A(CAT(TAG.I(_class="icon-road"), " %s" %  T('Traffic monitoring')),_href='http://traffic.integreen-life.bz.it', _title="Bluetooth traffic monitoring"), False, None),
	]),
	(T('Graph'), request.function == 'plot' , URL('plot', 'index'))
]
if session.auth and auth.is_logged_in():
	response.menu.insert(1, (T('manage'), False, None, [
		(T('Add station'), False, URL('default', 'add_station')),
		(T('Add log'), False, URL('default', 'add_log'))]))
