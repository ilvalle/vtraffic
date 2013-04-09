def index():
	stations = db(db.station).select(db.station.ALL)
	return {'stations':stations, 'station_id':15}

def get_history():
	from datetime import datetime, timedelta
	from itertools import groupby
	if not(request.ajax): raise HTTP(403)
	station_id = request.args(0) or 'index'
	#n_days = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 7
	n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1
	if not(station_id and station_id.isdigit()): raise HTTP(404)
	now = request.now
	#days_back = now - timedelta(days=n_days)
	epoch = db.record.gathered_on.epoch()
	import time
	t0 = time.time()	
	data = db(	(db.record.station_id == station_id) 
				#& (db.record.gathered_on >= days_back) 
				#& (db.record.gathered_on <= request.now)
			).select(epoch, cache=(cache.memcache, 3600))
	t1 = time.time()
	output = []
	for key, group in groupby(data, lambda x: x[epoch] / ( 60 * 60 * n_hours)):
		l = list(group)
		for l in group:
			print l[epoch]
		output.append( [ key*60*60*1000*n_hours, len(l)] ) 
	t2 = time.time()
	#print 'T', t2-t0, 't0', t1-t0, 't1', t2-t1
	return response.render('generic.json', {'station_%s' % station_id:{'data':output, 'station_id':station_id}})	
