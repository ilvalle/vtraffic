def emission_intime():
    table='elaborationhistory'
    period=3600         # Period of the result
    input_period=1800   # Period of the input data 
    output_type_id = 42 # Reference type_id (PM10)
    
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Streetstation'
    station_id=db_intime(db_intime.station).select(db.station.id, cacheable=True, limitby=(0,1), orderby=db.station.id).first().id
    
    ### check last value timestamp or set it as min(gathered_on)
    last_ts = db_intime.get_last_ts(output_type_id, station_id, period, table)
    unique = True
    if last_ts:
        last_ts = "'%s'" % (last_ts - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(timestamp)::date'
        unique = False # Speedup, no data are in the db for the given combination of station_id/type_id/interval

    last_ts = "'2014-09-16 08:00'"
    # The following query assign the emission factor for each path of the 'grafo stradale'
    # the data starts from the traffic monitoring detector (bluetooth/spira)
    query = """
    SELECT id_arco as station_id, start, end_time, n_vehicle_l * factor as light_vehicle, n_vehicle_h* factor as heavy_vehicle, n_vehicle_l, n_vehicle_h, factor,  ii.speed_default
    FROM (
	    (SELECT station_id, start_time AS start, end_time, count(a.id) AS n_element, sum(vehicle) as n_vehicle_l, sum(vehicles_heavy) as n_vehicle_h
	     FROM ( (SELECT start_time, lead(start_time, 1, '1070-01-01 00:00:00') OVER (ORDER BY start_time) AS end_time
	             FROM ( SELECT generate_series(%(last_ts)s, max(timestamp), '%(period)s seconds'::interval) AS start_time 
		                FROM intime.elaborationhistory
		                WHERE type_id = %(type_id_light)s and value!=0
		                LIMIT 2) x) as g
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
    ORDER  BY start asc
    """ % {'type_id_light':14, 'type_id_heavy':13, 'input_period':input_period, 'period':period, 
           'last_ts':last_ts, 'table':table}
    rows = db_intime.executesql(query, as_dict=True)

    # get the speed if available for the given arco, otherwise use default
    for r in rows:
        # Find the linkstations that belong to the given arco stradale
        link_stations = db_intime((db_intime.streetbasicdata.station_id == r['station_id']) &
                                  (db_intime.linkbasicdata.street_ids_ref.contains(db_intime.streetbasicdata.id))).select(db_intime.linkbasicdata.station_id, 
                                                                                                                          orderby=db_intime.linkbasicdata.station_id,
                                                                                                                          cacheable=True)
        link_stations = [l['station_id'] for l in link_stations]
        # Check the speed value (type_id=54) and compute the average if more than one linkstations affect the given 'arco'
        eh = db_intime.elaborationhistory
        speed = db_intime((eh.type_id == 54) & 
                          (eh.timestamp > r['start']) & (eh.timestamp < r['end_time']) &
                          (eh.period == 900) &
                          (eh.station_id.belongs(link_stations))).select(eh.value.avg(), cacheable=True).first()[eh.value.avg()]

        if speed:
            r['speed_default'] = speed

    inquinanti_ids = db_intime(db_intime.copert_emisfact).select(db_intime.copert_emisfact.type_id, groupby=db_intime.copert_emisfact.type_id, orderby=db_intime.copert_emisfact.type_id, cacheable=True)
    inquinanti_ids = [ i[db_intime.copert_emisfact.type_id] for i in inquinanti_ids]
    # ciclo su tutti gli archi (streetstation) valorizzati prima
    for r in rows:
        v = r["speed_default"]			## intime.trafficstreetfactor.vel_default
        nh = r["heavy_vehicle"]            ## intime.elaborationhistory.type=14
        nl = r["light_vehicle"]            ## intime.elaborationhistory.type=13
        for inq_type_id in inquinanti_ids:			## ciclo su ogni inquinante
            em_tot = 0
            pm_fe = db_intime( (db_intime.copert_emisfact.copert_parcom_id == db_intime.copert_parcom.id) &
                               (db_intime.copert_emisfact.type_id == inq_type_id)).select(cacheable=True)
            for ip in pm_fe:		## ciclo su ogni classe di veicolo
                eml = emh = 0
                idclass = ip["copert_parcom.id_class"]
                percent = ip["copert_parcom.percent"]
                a = ip["copert_emisfact.coef_a"]
                b = ip["copert_emisfact.coef_b"]
                c = ip["copert_emisfact.coef_c"]
                d = ip["copert_emisfact.coef_d"]
                e = ip["copert_emisfact.coef_e"]
                fe = (a+b*v+c*v*v)/(1+d*v+e*v*v)
                if (idclass==1) or (idclass==5): ## calcolo emissioni per veicoli leggeri
                    eml = fe*percent/100*nl  ##
                else:                            ## calcolo emissioni per veicoli pesanti
                    emh = fe*percent/100*nh  ##
                em_tot += (emh+eml)        ## calcolo emissione totale per ogni arco, per ogni inquinante per tutte le classi di veicolo

            print r['station_id'], inq_type_id, em_tot
            #db_intime.save_elaborations([{'value':em_tot, 'timestamp':r['start']}], r['station_id'], inq_type_id, 3600)
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