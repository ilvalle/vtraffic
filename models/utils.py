from collections import OrderedDict
import datetime
openstreatmap_static_link="http://ojw.dev.openstreetmap.org/StaticMap/?lat=%(lat)s&lon=%(lon)s&mlat0=%(lat)s&att=none&mlon0=%(lon)s&z=%(zoom)s&h=%(height)s&w=%(width)s&layer=mapnik&mode=Export&show=1"
CACHE_TIME_EXPIRE=300


def get_static_img(lat, lon, width='170', height='170', zoom=14):
	if not(lat and lon): return ''
	url = openstreatmap_static_link % {'lon':lon, 'lat':lat, 'height':150, 'width':width, 'zoom':zoom}
	return str(IMG(_src=url, _title="map"))

if request.controller == 'console':
    requested_period = 3600
    PERIODS=OrderedDict([('1800', T('30 minutes')), 
                         ('3600', T('1 hour')), 
                         ('10800', T('3 hours')), 
                         ('1', T('1 day'))])
else:
    requested_period = 7
    PERIODS=OrderedDict([('1800', T('30 minutes')), 
                         ('3600', T('1 hour')), 
                         ('10800', T('3 hours')), 
                         ('1', T('1 day')), 
                         ('7', T('1 week')), 
                         ('30', T('1 month')), 
                         ('90', T('3 months')), 
                         ('150', T('5 months')),
                         ('365', T('1 year'))])


    if request.vars.period:
    #	print request.vars.period
	    requested_period = int(request.vars.period) if request.vars.period.isdigit() else 7
	    if not ("%s" % requested_period in PERIODS):
		    requested_period = 30

if requested_period > 1000:
    period_limit = request.now - datetime.timedelta(seconds=requested_period)
else:
    period_limit = request.now - datetime.timedelta(days=requested_period)
start = db.record.with_alias('start_point')
end = db.record.with_alias('end_point')


def roundTime(dt=None, roundTo=60):
    """Round a datetime object to any time laps in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if dt == None : dt = datetime.datetime.now()
    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    # -1 is to round to the lower interval
    rounding = ((seconds-1)+roundTo/2) // roundTo * roundTo
    return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)
