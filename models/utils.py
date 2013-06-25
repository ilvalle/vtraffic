from collections import OrderedDict
import datetime
openstreatmap_static_link="http://ojw.dev.openstreetmap.org/StaticMap/?lat=%(lat)s&lon=%(lon)s&mlat0=%(lat)s&att=none&mlon0=%(lon)s&z=%(zoom)s&h=%(height)s&w=%(width)s&layer=mapnik&mode=Export&show=1"

def get_static_img(lat, lon, width='170', height='170', zoom=14):
	if not(lat and lon): return ''
	url = openstreatmap_static_link % {'lon':lon, 'lat':lat, 'height':150, 'width':width, 'zoom':zoom}
	return str(IMG(_src=url, _title="map"))

PERIODS=OrderedDict([('1', T('1 day')), ('7', T('1 week')), ('30', T('1 month')), ('90', T('3 month'))])

requested_period = 90
if request.vars.period:
	print request.vars.period
	requested_period = int(request.vars.period) if request.vars.period.isdigit() else 90
	if not ("%s" % requested_period in PERIODS):
		requested_period = 90

period_limit = request.now - datetime.timedelta(days=requested_period)



