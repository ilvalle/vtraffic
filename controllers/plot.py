from itertools import groupby
from datetime import timedelta
import time
from gluon.tools import prettydate

db.record._common_filter = lambda query: db.record.gathered_on > period_limit
db.match._common_filter = lambda query: db.match.gathered_on_orig > period_limit
db.station._common_filter = lambda query: db.station.dtype == 'Bluetoothstation'
db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Bluetoothstation'
db_intime.measurementstring._common_filter = lambda query: db_intime.measurementstring.timestamp > period_limit
db_intime.elaborationhistory._common_filter = lambda query: db_intime.elaborationhistory.timestamp > period_limit

if request.function != 'wiki':
    from gluon.tools import Wiki
    response.menu += Wiki(auth).menu(controller="default", function="wiki")

#@cache('plot_index_%s' % (requested_period), time_expire=5000, cache_model=cache.memcache)
def index():
    m = db_intime.measurementstring
    stations = db_intime(db_intime.station.id == m.station_id).select(db_intime.station.ALL,
                                                                      groupby=db_intime.station.ALL,
                                                                      cacheable=True)
    return response.render('plot/index.html', {'stations':stations, 'station_id':stations.first().id})

station_id = request.args(0) or 'index'
n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1

#@cache('get_history_%s_%s_%s' % (station_id, n_hours, requested_period), time_expire=300, cache_model=cache.memcache)
def get_history():
    session.forget()
    if not(request.ajax): raise HTTP(403)
    station_id = request.args(0) or 'index'
    n_hours = int(request.vars.interval) if request.vars.interval and request.vars.interval.isdigit() else 1
    station = db_intime(db_intime.station.id == station_id).select(db_intime.station.name, cacheable=True)
    if not(station_id and station_id.isdigit()) or len(station) != 1: raise HTTP(404)
    station = station.first()
    eh = db_intime.elaborationhistory
    rows = db_intime( (eh.station_id == station_id) &
                      (eh.type_id == 19) &
                      (eh.period  == (n_hours * 1800))).select(eh.value,eh.timestamp.epoch(), orderby=~eh.timestamp, cacheable=True)

    output = []
    for key, group in groupby(rows, lambda x: (x[eh.timestamp.epoch()]) / ( 60 * 60 * n_hours)):
        output.append( [ key*60*60*1000*n_hours, sum(r[eh.value] for r in list(group))] )

    series = [{'data':output, 'id': 'station_%s' % station_id, 'station_id':station_id, 'label': station.name}]    if len(output) != 0 else []
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

def get_real_time():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Linkstation'
    stations = db_intime(db_intime.station).select(db_intime.station.ALL)
    modes = []
    eh = db_intime.elaborationhistory
    time_limit = request.now - datetime.timedelta(seconds=5400)
    for station in stations:
        rows = db_intime( (eh.type_id == 918) &
                          (eh.station_id == station.id) & 
                          (eh.period == 900) &
                          (eh.timestamp > time_limit)
                          ).select(eh.ALL, orderby=~eh.timestamp, limitby=(0,2))
        if len(rows)<2:
            continue
        modes.append({'mode': rows[0].value, 'mode_ts': rows[0].timestamp, 'mode_prev': rows[1].value, 'string':str(datetime.timedelta(seconds=rows[0].value)), 'station': station})

    return response.render('plot/tab_real_time.html', {'modes':modes} )
   
@cache('get_geojson_stations', time_expire=80000, cache_model=cache.memcache)
def get_geojson_stations():
    from gluon.serializers import loads_json
    rows= db(db.station).select(db.station.lat, db.station.lgt, db.station.name)
 
    features= [{"type": "Feature",
                "properties": {
                    "popupContent": r[db.station.name]
                },
                "geometry": {"type": "Point", "coordinates": [r[db.station.lgt], r[db.station.lat]]} } for r in rows] 
 
    return response.json({"type": "FeatureCollection", 'features': features})
