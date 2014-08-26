def create_matches():
    return run_all_intime()

### For each bluetooth station, count the number of bluetooth gathered in a window of @interval seconds
def count_bluetooth_intime(interval=900):
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Bluetoothstation'
    output_type_id = 19      # Elaboration type is 19
    input_type_id = 15       # Bluetooth detection type_id
    total = count_elements_intime(interval=interval,
                                  output_type_id=output_type_id,
                                  input_type_id=input_type_id,
                                  input_table='intime.measurementstringhistory')
    return total

### For each link station, count the number of match in a window of @interval seconds
def count_match_intime(interval=900):
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Linkstation'
    output_type_id = 920     # Bluetooth count match
    input_type_id = 921      # Bluetooth match
    total = count_elements_intime(interval=interval,
                                  output_type_id=output_type_id,
                                  input_type_id=input_type_id,
                                  input_table='intime.elaborationhistory')
    return total

### For each link station, count the number of match in a window of @interval seconds
def run_mode_intime(interval=900):
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Linkstation'
    stations = db_intime(db_intime.station.id).select(cacheable=True, limitby=(0,1),)
    total = 0
    output_type_id = 918      # Elapsed time
    input_type_id = 921       # Bluetooth match
    for s in stations:
        total += compute_mode_intime(station_id=s.id,
                                     interval=interval,
                                     output_type_id=output_type_id, 
                                     input_type_id=input_type_id,
                                     input_table='intime.elaborationhistory')
    return total

### Generic method to count the number of element in a window of @interval seconds for a given table
def count_elements_intime(interval, output_type_id, input_type_id, input_table):
    stations = db_intime(db_intime.station).select(db_intime.station.id, cacheable=True)
    total = 0
    for s in stations:
        print 'station ', s.id
        total += __count_elements_intime(station_id=s.id, 
                                         interval=interval,
                                         output_type_id=output_type_id, 
                                         input_type_id=input_type_id,
                                         input_table=input_table)
    return total

def __count_elements_intime(station_id, interval, output_type_id, input_type_id, input_table):
    ### check last value timestamp or set it as min(gathered_on)
    last_ts = db_intime.get_last_ts(output_type_id, station_id, interval, 'elaborationhistory')
    unique = True
    if last_ts:
        last_ts = "'%s'" % (last_ts - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(timestamp)::date'
        unique = False # Speedup, no data are in the db for the given combination of station_id/type_id/interval

    query = """
        SELECT start_time AS timestamp, count(e.id) AS value
        FROM (
           SELECT start_time, lead(start_time, 1, now()::timestamp) OVER (ORDER BY start_time) AS end_time
           FROM ( SELECT generate_series(%(since)s, max(timestamp), '%(interval)s seconds'::interval) AS start_time 
                  FROM %(table)s
                  WHERE station_id = %(station_id)s and type_id = %(type_id)s
                  ORDER BY start_time ASC
                  LIMIT 10000 ) x
           ) as g
           left JOIN (select timestamp, id 
                      from %(table)s
                      where station_id = %(station_id)s and type_id = %(type_id)s) e 
           ON e.timestamp >= g.start_time AND e.timestamp < g.end_time
        GROUP  BY start_time
        ORDER  BY start_time asc;
    """ % {'station_id': station_id, 'since': last_ts, 'interval':interval, 'type_id':input_type_id, 'table':input_table}
    rows = db_intime.executesql(query, as_dict=True)
    # Adapt the result to be stored
    #rows = [{'timestamp': r['timestamp'], 'value':r['n_elements'] } for r in rows]
    # Save the data
    db_intime.save_elaborations(rows, station_id, output_type_id, interval, unique)

    return len(rows)

## Set all record to valid=False if there are null mac address
#def run_valid_record():
#    db_intime.measurementstringhistory._common_filter = lambda query: (db_intime.measurementstringhistory.type_id == 55)
#    rows = db((db_intime.measurementstringhistory.value == '00:00:00:00:00:00') & (db_intime.measurementstringhistory.valid == None)).select(db_intime.measurementstringhistory.ALL)
#    for r in rows:
#        r.update_record(valid=False)
#    db.commit()
#    return len(rows)

### Generic method to count the number of element in a window of @interval seconds for a given table
def compute_mode_intime(station_id, interval, output_type_id, input_type_id, input_table):
    ### check last value timestamp or set it as min(gathered_on)
    last_ts = __get_last_ts(output_type_id, station_id, interval, 'elaborationhistory')
    if last_ts[db_intime.elaborationhistory.timestamp.max()]:
        last_ts = "'%s'" % (last_ts[db_intime.elaborationhistory.timestamp.max()] - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(timestamp)::date'

    query = """
        SELECT start_time, end_time, timestamp, e.value
        FROM (
           SELECT start_time, lead(start_time, 1, now()::timestamp) OVER (ORDER BY start_time) AS end_time
           FROM ( SELECT generate_series(%(since)s, max(timestamp), '%(interval)s seconds'::interval) AS start_time 
                  from %(table)s
                  where station_id = %(station_id)s and type_id = %(type_id)s) x
           ) as g
           left JOIN (select timestamp, id, value
                      from %(table)s
                      where station_id = %(station_id)s and type_id = %(type_id)s) e 
           ON e.timestamp >= g.start_time AND e.timestamp < g.end_time
        WHERE e.value IS NOT NULL
        ORDER  BY start_time asc;
    """ % {'station_id': station_id, 'since': last_ts, 'interval':interval, 'type_id':input_type_id, 'table':input_table}
    rows = db_intime.executesql(query, as_dict=True) 

    list_blocks = __split_rows_2time_frame(rows)
    rows = __wrapper_elaboration_intime( list_blocks,
                                  __mode_intime,
                                  interval, 
                                  vertical_block_seconds=30)
                            
    # Adapt the result to be stored
    rows = [{'timestamp': r[0], 'value':r[1] } for r in rows]
    # Save the data
    #db_intime.save_elaborations(rows, station_id, output_type_id, interval)

    return len(rows)

# Return matches grouped to the specific time_frame they belong to 
def __split_rows_2time_frame(rows):
    f = lambda row: row['start_time']
    return [list(group) for key, group in groupby(rows, f)]

# This skeleton allows to run easily statistical analysis across rows splitted into frames
def __wrapper_elaboration_intime( blocks_list, 
                                  function, 
                                  block_seconds=900, 
                                  vertical_block_seconds=30):
    output = []
    prev   = None
    for block in blocks_list:
        if len(block) <= 2:		# two values are not enough, let pass
            continue
        current = block[0]
#        seconds = epoch_orig - (block[0].epoch_orig % block_seconds)		
        seconds = current['start_time']
     
        if prev and current['timestamp'] > (prev['timestamp'] + datetime.timedelta(seconds=(block_seconds*3))):	#fill the gap with two empty values
            output.append ( [ prev_seconds + datetime.timedelta(seconds=(block_seconds + block_seconds/2)), 0] )
            output.append ( [ seconds - datetime.timedelta(seconds=(block_seconds/2)), 0] )

        value = function(block, block_seconds, vertical_block_seconds)
        #output.append ( [(seconds + block_seconds/2), value] )
        output.append ( [seconds, value] )
        prev, prev_seconds = current, seconds
    return output
	
# return the mode along a list of rows (block)
def __mode_intime(block, block_seconds=0, vertical_block_seconds=0):
	block = sorted(block, key=operator.itemgetter('value'))
	initial_time_frame = block[0]['value']
	end_time_frame     = block[-1]['value']
	mode_value = {'counter':0, 'seconds':0}
	i = 0
	for second in range(0,int(end_time_frame-initial_time_frame), MODE_STEP):
		current_initial = initial_time_frame + second
		current_end     = current_initial + vertical_block_seconds
		counter = 0
		while i < len(block):
			ele = block[i]
			if current_initial <= ele['value'] < current_end:
				counter = counter + 1 
			elif current_end < ele['value']:
				break
			i = i + 1
		if counter > mode_value['counter']:
			mode_value['counter'] = counter
			mode_value['seconds'] = current_initial
	
	if mode_value['seconds'] == 0:
		value = 0
	else:
		value = mode_value['seconds'] + (vertical_block_seconds/2)
	return value
