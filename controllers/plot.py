from itertools import groupby
from datetime import timedelta
import time

db.record._common_filter = lambda query: db.record.gathered_on > period_limit
db.match._common_filter = lambda query: db.match.gathered_on_orig > period_limit

if request.function != 'wiki':
	from gluon.tools import Wiki
	response.menu += Wiki(auth).menu(controller="default", function="wiki")

@cache('plot_index_%s' % (requested_period), time_expire=5000, cache_model=cache.memcache)
def index():
	stations = db(db.station.id == db.record.station_id).select(db.station.ALL,
                                                                groupby=db.station.ALL,
                                                                orderby=~db.record.station_id.count(),
                                                                cacheable=True)
	return response.render('plot/index.html', {'stations':stations, 'station_id':stations.first().id})

station_id = request.args(0) or 'index'
n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1

@cache('get_history_%s_%s_%s' % (station_id, n_hours, requested_period), time_expire=300, cache_model=cache.memcache)
def get_history():
    session.forget()
    if not(request.ajax): raise HTTP(403)
    station_id = request.args(0) or 'index'
    n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1
    station = db(db.station.id == station_id).select(db.station.name, cacheable=True, cache=(cache.memcache, 80000))
    if not(station_id and station_id.isdigit()) or len(station) != 1: raise HTTP(404)
    station = station.first()

    query = db( (db.record.station_id == station_id) )._select(db.record.utc_in_ms,
                                                               orderby=db.record.utc_in_ms)
    data = db.executesql(query, as_dict=True)

    output = []
    for key, group in groupby(data, lambda x: (x['utc_in_ms']) / ( 60 * 60 * n_hours * 1000)):
        output.append( [ key*60*60*1000*n_hours, len(list(group))] )

    series = [{'data':output, 'id': 'station_%s' % station_id, 'station_id':station_id, 'label': station.name}]	if len(output) != 0 else []
    return response.json({'series': series})

@cache('figures_%s' % requested_period, time_expire=80000, cache_model=cache.memcache)
def figures():
	session.forget()
	stations = db(db.station).select(db.station.id, db.station.name, cache=(cache.ram, 3600))

	output=[]
	for station in stations:

		unique_mac = db( (db.record.station_id == station.id) ).select( db.record.mac.count(True), 
                                                                        cacheable=True)

		day = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day()  
		values = db( (db.record.station_id == station.id) ).select( db.record.id.count(),
                                                                    groupby=day,
                                                                    cacheable=True)
		cur_station = {}
		cur_station['name']= station.name

		if  len(values):
			cur_station['min'] = min(values, key=lambda x: x['_extra'][db.record.id.count()])['_extra'][db.record.id.count()] 
			cur_station['max'] = max(values, key=lambda x: x['_extra'][db.record.id.count()])['_extra'][db.record.id.count()] 
			cur_station['total_detected'] = sum(v['_extra'][db.record.id.count()] for v in values)
			cur_station['avg'] = cur_station['total_detected'] / len(values) 
			cur_station['active'] = T('active')
			cur_station['unique_detected'] = unique_mac[0][db.record.mac.count(True)]
			output.insert(0, cur_station)
		else: 
			cur_station['min'] = '--'
			cur_station['max'] = '--'
			cur_station['avg'] = '--'
			cur_station['total_detected'] = '--'
			cur_station['active'] = T('disabled')
			cur_station['unique_detected'] = '--'
			output.append(cur_station)
	return response.render('plot/figures.html', {'stations':output} )

def flow():
    station_id = 19 # castel firmiano
    stations = db( db.match.station_id_orig == db.station.id ).select(db.station.name, db.station.id, groupby=db.station.name|db.station.id).as_list()
    links = []
    exclude_backwards = set()
    ele = next((item for item in stations if item["id"] == 19), None)

    stations.insert(0, stations.pop(stations.index(ele)))
    for pos_orig, station_orig in enumerate( stations):
        exclude_backwards.add( station_orig['id'])
        for pos_dest, station_dest in enumerate(stations):
            if station_dest['id'] in exclude_backwards: continue
            query = db( (db.match.station_id_orig == station_orig['id']) &
                        (db.match.station_id_dest == station_dest['id']))._count()
            data = db.executesql(query, as_dict=True)
            n_match = data[0]['count']
            if n_match != 0:
                links.append({'source': pos_orig, 'target': pos_dest, 'value': str(n_match)})

    #stations = [{'name': station['name']} for station in stations]
   # links.append({'source': 2, 'target': 5, 'value': 333})
    return response.json({'links':links, 'nodes':stations})
  
