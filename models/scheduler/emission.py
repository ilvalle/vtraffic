import time
from itertools import groupby
import math

def emission_intime():
    table='elaborationhistory'
    period=3600         # Period of the result
    input_period=1800   # Period of the input data 
    output_type_id = 42 # Reference type_id (PM10)

    inquinanti_ids = db_intime(db_intime.copert_emisfact).select(db_intime.copert_emisfact.type_id,
                                                                 groupby=db_intime.copert_emisfact.type_id,
                                                                 orderby=db_intime.copert_emisfact.type_id, cacheable=True)
    inquinanti_ids = [ i[db_intime.copert_emisfact.type_id] for i in inquinanti_ids]

    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Streetstation'
    # Find out the most recent timestamp for a given set of types
    last_ts=db_intime( (db_intime.station.id == db_intime.elaborationhistory.station_id) &
                       (db_intime.elaborationhistory.type_id.belongs(inquinanti_ids)) ).select(db_intime.elaborationhistory.timestamp.max(),
                                                                                               cacheable=True).first()[db_intime.elaborationhistory.timestamp.max()]

    unique = True
    if last_ts:
        last_ts = "'%s'" % roundTime(last_ts, period) #% (last_ts - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(timestamp)::date'
        last_ts = "'2014-09-16 06:00:00'"   # Debug purposes
        unique = False # Speedup, no data are in the db for the given combination of station_id/type_id/interval

    # The following query assign the emission factor for each path of the 'grafo stradale'
    # the data starts from the traffic monitoring detector (bluetooth/spira)
    # debug    SELECT id_arco as station_id, start, end_time, n_vehicle_l * factor as light_vehicle, n_vehicle_h* factor as heavy_vehicle, n_vehicle_l, n_vehicle_h, factor,  ii.speed_default
    # last_ts = "'2014-09-16 06:00:00'"
    import time
    t0 = time.time()
    query = """
    SELECT id_arco as station_id, start, end_time, n_vehicle_l * factor as light_vehicle, n_vehicle_h* factor as heavy_vehicle, ii.speed_default
    FROM (
	    (SELECT station_id, start_time AS start, end_time, count(a.id) AS n_element, sum(vehicle) as n_vehicle_l, sum(vehicles_heavy) as n_vehicle_h
	     FROM ( (SELECT start_time, lead(start_time, 1, '1070-01-01 00:00:00') OVER (ORDER BY start_time) AS end_time
	             FROM ( SELECT generate_series(%(last_ts)s, max(timestamp), '%(period)s seconds'::interval) AS start_time 
		                FROM intime.elaborationhistory
		                WHERE type_id = %(type_id_light)s and value!=0
		                LIMIT 200) x) as g
	            LEFT JOIN (SELECT station_id, timestamp, id, value as vehicle, type_id
			               FROM intime.elaborationhistory
			               WHERE (type_id = %(type_id_light)s) and period = %(input_period)s) e
	            ON e.timestamp >= g.start_time AND e.timestamp < g.end_time) a
	            INNER JOIN (SELECT value as vehicles_heavy, timestamp
			                FROM intime.elaborationhistory
			                WHERE (type_id = %(type_id_heavy)s) and period = %(input_period)s) d
	            ON a.timestamp = d.timestamp
	     GROUP  BY station_id, start_time, end_time
	     ORDER  BY start_time asc) aa
	     INNER JOIN intime.trafficstreetfactor as t
	     ON t.id_spira = aa.station_id) i
	     INNER JOIN intime.streetbasicdata ii
	     ON ii.station_id = i.id_arco
    ORDER  BY start asc, station_id asc
    """ % {'type_id_light':14, 'type_id_heavy':13, 'input_period':input_period, 'period':period, 
           'last_ts':last_ts, 'table':table}
    rows = db_intime.executesql(query, as_dict=True)

    eh = db_intime.elaborationhistory
    # get the speed if available for the given arco, otherwise use default
    for r in rows:
        # Find the linkstations that belong to the given arco stradale
        link_stations = db_intime((db_intime.streetbasicdata.station_id == r['station_id']) &
                                  (db_intime.linkbasicdata.street_ids_ref.contains(db_intime.streetbasicdata.id))).select(db_intime.linkbasicdata.station_id, 
                                                                                                                          orderby=db_intime.linkbasicdata.station_id,
                                                                                                                          cacheable=True)
        link_stations = [l['station_id'] for l in link_stations]
        # Check the speed value (type_id=54) and compute the average if more than one linkstations affect the given 'arco'

        speed = db_intime((eh.type_id == 54) & 
                          (eh.timestamp > r['start']) & (eh.timestamp < r['end_time']) &
                          (eh.period == 900) &
                          (eh.station_id.belongs(link_stations))).select(eh.value.avg(), cacheable=True).first()[eh.value.avg()]

        if speed:
            r['speed_default'] = speed

    # ciclo su tutti gli archi (streetstation) valorizzati prima
    # Get once all values
    pm_fe_dict = {}
    for inq_type_id in inquinanti_ids:
        pm_fe_dict[inq_type_id] = db_intime( (db_intime.copert_emisfact.copert_parcom_id == db_intime.copert_parcom.id) &
                                             (db_intime.copert_emisfact.type_id == inq_type_id)).select(cacheable=True)

    for r in rows:
        v = r["speed_default"]             ## intime.trafficstreetfactor.vel_default
        nh = r["heavy_vehicle"]            ## intime.elaborationhistory.type=14
        nl = r["light_vehicle"]            ## intime.elaborationhistory.type=13
        last_24_h = r['start'] - datetime.timedelta(days=24)
        for inq_type_id in inquinanti_ids:			## ciclo su ogni inquinante
            em_tot = 0
            if (nl != 0) and (nh != 0):
                pm_fe = pm_fe_dict[inq_type_id]
                for ip in pm_fe:		## ciclo su ogni classe di veicolo
                    #em = 0              #useless
                    ce = ip.copert_emisfact
                    cp = ip.copert_parcom
                    idclass = cp.id_class
                    percent = cp.percent
                    a = ce.coef_a
                    b = ce.coef_b
                    c = ce.coef_c
                    d = ce.coef_d
                    e = ce.coef_e
                    fe = (a+b*v+c*v*v)/(1+d*v+e*v*v)
                    if (idclass==1) or (idclass==5): ## calcolo emissioni per veicoli leggeri
                        em = fe*percent/100*nl  ##
                    else:                            ## calcolo emissioni per veicoli pesanti
                        em = fe*percent/100*nh  ##
                    em_tot += em        ## calcolo emissione totale per ogni arco, per ogni inquinante per tutte le classi di veicolo
            else:
                # 0 vehicles during night are estinated, otherwise (day) skip
                if ((r['start'].time() >= datetime.time(22,00)) or (r['start'].time() < datetime.time(06, 00))):
                    # Take the average of the last 24h
                    value = db_intime( (eh.type_id == inq_type_id) &
                                       (eh.station_id == r['station_id']) &
                                       (eh.period == period) &
                                       (eh.value != 0) &
                                       (eh.timestamp > last_24_h)).select(eh.value.avg(), cacheable=True).first()[eh.value.avg()]
                    if value:
                        em_tot = (value/100) * 6.5
                    #print r['station_id'], r['start'], em_tot
                else:
                    continue
            db_intime.save_elaborations([{'value':em_tot, 'timestamp':r['start']}], r['station_id'], inq_type_id, period, commit=False)
        #print r['station_id']
    db_intime.commit()
    t2 = time.time()
    #print t2-t0
    return len(rows)

# Compute the speed for all link stations
# TODO cycle over all possible period, not only 900.
def compute_bspeed():
    stations = db_intime(db_intime.linkbasicdata).select(cacheable=True)
    input_type_id = 918       # Elapsed time
    output_type_id = 54       # Speed
    eh = db_intime.elaborationhistory
    tot=0
    for station in stations:
        period = 900
        query = ((eh.type_id == input_type_id) &
                 (eh.station_id == station.station_id) &
                 (eh.period == period) &
                 (eh.value != 0))
        last_ts = db_intime.get_last_ts(output_type_id, station.station_id, period, 'elaborationhistory')
        if last_ts:
            last_ts = roundTime(last_ts, period)
            query &= (eh.timestamp >= last_ts)
        elapsed_times = db_intime(query).select(eh.timestamp, eh.value, cacheable=True)
        rows_speed = [{'timestamp': r['timestamp'], 'value': 0 if not(r['value']) else ((station.length / r['value'])*3.6) } for r in elapsed_times]
        db_intime.save_elaborations(rows_speed, station.station_id, output_type_id, period, True if last_ts else False, update_ts=False)
        tot += len(rows_speed)
    return tot

# Read all valid values from measurementmobilehistory
def filter_vehicle_data():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Mobilestation'
    vehicles = db_intime(db_intime.station).select(cacheable=True)
    tot = ''
    for v in vehicles:
        if v.stationcode == 1:
            db_intime.measurementmobilehistory._common_filter = lambda query: db_intime.measurementmobilehistory.station_id == v.id
            tot += __filter_vehicle_data() + "</br>"
    return tot

def __filter_vehicle_data():
### 1' elaboration: MOVING AVERAGE
    tot = 0
    t0 = time.time()
    mmh = db_intime.measurementmobilehistory
    mh = db_intime.measurementhistory
    delay = 12
    temporalWindowWidth = 7
    offset = 0
    query = (mmh.no2_1_ppb != None)
    # Find the last value stored by a former elaboration
    last_ts = db_intime(mmh.no2_1_microgm3_ma).select(mmh.ts_ms.max(), cacheable=True).first()[mmh.ts_ms.max()]

    if last_ts:
        query &= (mmh.ts_ms > (last_ts - datetime.timedelta(seconds=max(delay,temporalWindowWidth))))

    rows = db_intime(query).select(mmh.id, mmh.no2_1_ppb, mmh.ts_ms,  mmh.gps_1_speed_mps, mmh.ts_ms.epoch(), mmh.no2_1_microgm3_ma, limitby=(0,50000), orderby=mmh.ts_ms.epoch())
    t1 = time.time()

    # Parameters to convert from ppb to microgm3
    NO2MolarWeight = float(46.00449)
    T_0 = float(273)    ## it is the reference temperature in [°K], equal to 0 [°C]
#    T_1 = float(277)    ## it is the current temperature in [°K]. During the measurements, T_air measured by the meteo station has been on average 4 [°C]
    V_0 = float(22.414) ## it is the molar volume in [l/mol] at the conditions (T_0, P_0 = 1013 [kPa])
    type_id_air_temperature = 8
#    f = lambda r: r[mmh.ts_ms.epoch()] // 3600        # one hour
#    for key, group in groupby(rows, f):
#        d = datetime.datetime.fromtimestamp(key*3600+3600)
#        row = db_intime((mh.type_id == type_id_air_temperature) &
#                        (mh.timestamp < d)).select(mh.value, mh.timestamp, orderby=~mh.timestamp,
#                                                   limitby=(0,1), cacheable=True).first()

#        T_1 = float(273 + row.value) if row.value else float(277)
#        for r in group:
#            r['no2_1_microgm3'] = (r.measurementmobilehistory.no2_1_ppb)
#            r['no2_1_microgm3_exp'] = 0
#            r['alpha'] = 0

    for r in rows:
        r['no2_1_microgm3'] = (r.measurementmobilehistory.no2_1_ppb)
        r['no2_1_microgm3_exp'] = 0
        r['alpha'] = 0


    last_ts  = datetime.datetime.fromtimestamp(0) if len(rows) == 0 else rows[0].measurementmobilehistory.ts_ms
    n_values = 0
    to_reject = 0
    total = 0
    alpha_exp = float(75)

    if len(rows) < max(delay,temporalWindowWidth):
        db_intime.commit()
        return 'postponed'

    # compute moving average
    # compute exponential negative filter
    for pos, r in enumerate(rows):
        # If there is a gap between two samples the value is not valid.
        # The delay is the amount of time occured by the air to be pumped in the pipe and to reach the no2 sensor detector.
        # if the is a gap, the first delay records (1per seconds) are rejected, after that we can start to accomulate data
        # when we have temporalWindowWidth records in the total, we can store the value.
        if r.measurementmobilehistory.ts_ms > (last_ts + datetime.timedelta(seconds=1800)):
            total = 0
            n_values = 0
            to_reject = delay
        else:
            to_reject -= 1

        last_ts = r.measurementmobilehistory.ts_ms
        if to_reject > 0:
            continue
        total += r['no2_1_microgm3']
        r['alpha'] = math.tanh( float(rows[pos].measurementmobilehistory.gps_1_speed_mps)/alpha_exp)
        n_values += 1
        values = {}
        if n_values == temporalWindowWidth +1:
            total -= rows[pos-temporalWindowWidth]['no2_1_microgm3']    # Remove the first value in the moving window
            n_values -= 1

        #moving average
        if n_values == temporalWindowWidth:
            values['no2_1_microgm3_ma'] = round((float(total)/temporalWindowWidth) - offset, 2)

        #exponential negative filter
        p=[0]*(temporalWindowWidth + 3)

        for i in xrange(1,temporalWindowWidth + 1, 1):
            p[i] = math.exp( -r['alpha'] * (i-1))
            r['no2_1_microgm3_exp'] += p[i] * rows[pos-(i-1)]['no2_1_microgm3']
        r['no2_1_microgm3_exp'] = float(r['no2_1_microgm3_exp'])/float(sum(p))
        values['no2_1_microgm3_exp'] = round(r['no2_1_microgm3_exp'], 2) - offset

        #Store computed values
        db_intime(mmh.id == r.measurementmobilehistory.id).update(**values)
    t2 = time.time()
    db_intime.commit()
    return "%s %s" % (len(rows), t2-t1)

