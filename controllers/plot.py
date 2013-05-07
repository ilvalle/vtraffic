from applications.vtraffic.modules.tools import EPOCH_M
from itertools import groupby
from datetime import timedelta

if request.function != 'wiki':
	from gluon.tools import Wiki
	response.menu += Wiki(auth).menu(controller="default", function="wiki")

 #@cache.action(time_expire=80000, cache_model=cache.memcache)
def index():
	stations = db(db.station).select(db.station.ALL)
	return response.render('plot/index.html', {'stations':stations, 'station_id':15})

station_id = request.args(0) or 'index'
n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1

@cache('get_history_%s_%s' % (station_id, n_hours), time_expire=80000, cache_model=cache.memcache)
def get_history():
	session.forget()
	if not(request.ajax): raise HTTP(403)
	station_id = request.args(0) or 'index'
	#n_days = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 7
	n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1
	station = db(db.station.id == station_id).select(db.station.name)
	if not(station_id and station_id.isdigit()) or len(station) != 1: raise HTTP(404)
	station = station.first()
	#now = request.now
	#days_back = now - timedelta(days=n_days)
	day = db.record.gathered_on.day()
	import time

	t0 = time.time()	
	data = db(	(db.record.station_id == station_id) 
				#& (db.record.gathered_on >= days_back) 
				#& (db.record.gathered_on <= request.now)
			).select(db.record.gathered_on, orderby=db.record.gathered_on) #, cache=(cache.memcache, 3600))
	t1 = time.time()
	output = []
	for key, group in groupby(data, lambda x: (EPOCH_M(x.gathered_on)) / ( 60 * 60 * n_hours)):
		output.append( [ key*60*60*1000*n_hours, len(list(group))] ) 
	t2 = time.time()
	#print 'T', t2-t0, 't0', t1-t0, 't1', t2-t1
	return response.render('generic.json', {'series': [{'data':output, 'id': 'station_%s' % station_id, 'station_id':station_id, 'label': station.name}]})


@cache('figures', time_expire=80000, cache_model=cache.memcache)
def figures():
	session.forget()
	stations = db(db.station).select(db.station.id, db.station.name, cache=(cache.ram, 3600))
	n_days = 7
	aggregation	= 60*60*24 # Daily aggregation
	days_back = request.now - timedelta(days=n_days)
	output=[]
	for station in stations:
		data = db(	(db.record.station_id == station.id) 
					& (db.record.gathered_on >= days_back) 
				).select(db.record.mac,db.record.gathered_on, orderby=db.record.gathered_on, cache=(cache.ram, 3600))
		values = []
		for key, group in groupby(data, lambda x: (EPOCH_M(x.gathered_on)) / ( aggregation )):
			l = list(group)
			values.append( {'detected':len(l), 'day':key*aggregation} ) 
		cur_station = {}
		cur_station['name']= station.name
		cur_station['min'] = min(values, key=lambda x: x['detected']) if len(values) else {'detected':'--', 'day':'0'}
		cur_station['max'] = max(values, key=lambda x: x['detected']) if len(values) else {'detected':'--', 'day':'0'}
		cur_station['avg'] = sum(v['detected'] for v in values) / len(values) if len(values) else '--'

		cur_station['total_detected'] = len(data) if len(values) else '--'
		cur_station['unique_detected'] = len( set(v[ db.record.mac] for v in data) ) if len(values) else '--'
		cur_station['active'] = 'active' if len(values) else 'disabled'		
		output.append(cur_station)

	return response.render('plot/figures.html', {'stations':output} )

