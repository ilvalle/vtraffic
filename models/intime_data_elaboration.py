# New methods for the intime model

start_intime = db_intime.measurementstringhistory.with_alias('start_point')
end_intime = db_intime.measurementstringhistory.with_alias('end_point')

def run_all_intime():
    output_type_id = 21 
    input_type_id = 15
    period = 1
    db_intime.station._common_filter = lambda query: (db_intime.station.stationtype == 'Linkstation')
    
    stations = db_intime(db_intime.station.id == db_intime.linkbasicdata.station_id).select(db_intime.linkbasicdata.ALL, 
                                                                                            orderby=db_intime.station.id, 
                                                                                            cacheable=True)
    total = 0
    for link in stations:
        matches = find_matches_intime(link, period, output_type_id, input_type_id)
        rows = [{'timestamp': m.start_point.timestamp, 'value':m.elapsed_time.total_seconds()} for m in matches]
        # Save the data
        total += db_intime.save_elaborations(rows, station_id=link.station_id, type_id=output_type_id, interval=period, unique=False)

    return total

def find_matches_intime (link_station, period, output_type_id, input_type_id):
    db_intime.measurementstringhistory._common_filter = lambda query: (db_intime.measurementstringhistory.type_id == input_type_id)
    # find last stored match for the given link station
    last_match_query = db_intime( (db_intime.elaborationhistory.station_id == link_station.station_id) &
                                  (db_intime.elaborationhistory.type_id == output_type_id) &
                                  (db_intime.elaborationhistory.period == period))._select(db_intime.elaborationhistory.ALL,
                                                                                           orderby=~(db_intime.elaborationhistory.timestamp.epoch() + db_intime.elaborationhistory.value),
                                                                                           limitby=(0,1) )

    last_match = db_intime.executesql(last_match_query, as_dict=True)
    query_od = (start_intime.station_id == link_station.origin) & (end_intime.station_id == link_station.destination)
    if last_match:
        match = last_match[0]

        dest_timestamp = match['timestamp'] + (datetime.timedelta(seconds=match['value']))
        initial_data = dest_timestamp - __next_step()

    matches = []
    n_prev_matches = 1
    while len(matches) != n_prev_matches:   #loop check
        n_prev_matches = len(matches)
        if last_match:
            # The constraint (end.gathered_on > initial_data) reduces the number of rows to sort before the left join
            query = query_od & (start_intime.timestamp > initial_data ) & (end_intime.timestamp > dest_timestamp)
#            query &= (end_intime.timestamp > dest_timestamp)  # Fix to avoid duplicated value, the destination must be higher than the last match
            initial_data = initial_data - __next_step()
            matches = __get_rows_intime(query, use_cache=False)
            matches = __clean_progress_matches_intime(matches, dest_timestamp)
        else:
            matches = __get_rows_intime(query_od, use_cache=False)
            n_prev_matches = len(matches)         # force to stop

    return matches    
    
def __get_rows_intime(query, use_cache=True, limitby=None):
    query_1 = query & ((end_intime.timestamp.epoch() - start_intime.timestamp.epoch()) < 3600)
    matches = db_intime( query_1 ).select(start_intime.ALL, end_intime.ALL,
                              orderby=start_intime.created_on,
                              left=start_intime.on( (start_intime.value == end_intime.value) & (start_intime.timestamp < end_intime.timestamp)),
                              limitby=limitby,
                              cacheable = True)

    matches = __remove_dup_intime(matches)	# Remove matches based on the same timestamp

    # Compute the elapsed_time
    for m in matches:
        m.elapsed_time = m.end_point.timestamp - m.start_point.timestamp   # TODO, DB elaboration?

    matches = __filter_twins_intime(matches) # Remove matches with the same elapsed_time at the same time
    return matches
	
def __remove_dup_intime(rows):
	hash_end = {}
	hash_start = {}
	remove=[]
	for pos, r in enumerate(rows):
		if r.start_point.id in hash_start:
			pos_prev = hash_start[r.start_point.id]
			prev = rows[pos_prev]
			if (r.end_point.timestamp < prev.end_point.timestamp):
				remove.append(pos_prev)			# remove the old one
				hash_start[r.start_point.id] = pos	# update the pos to the new one
			else:
				remove.append(pos)			# remove the current one
		else:
			hash_start[r.start_point.id] = pos			
		if r.end_point.id in hash_end:
			pos_prev = hash_end[r.end_point.id]
			prev = rows[pos_prev]
			if (r.start_point.timestamp > prev.start_point.timestamp):
				remove.append(pos_prev)			# remove the old one
				hash_end[r.end_point.id] = pos		# update the pos to the new one
			else:
				remove.append(pos)			# remove the current one
		else:
			hash_end[r.end_point.id] = pos

	rows = [r for pos, r in enumerate(rows) if pos not in remove]
	return rows
	
# Remove matches with the same elapsed_time computed at the same time (issue: vehicle with more than one device onboard)
def __filter_twins_intime(rows):
	out = []
	for pos, row in enumerate(rows):
		next = rows[pos + 1 ] if pos != len(rows) -1 else None
		if not (next) or row.start_point.timestamp != next.start_point.timestamp or row.elapsed_time != next.elapsed_time:
			out.append(row)
	return rows

# this constraint must be executed after remove_dup 
def __clean_progress_matches_intime(matches, destination_min_date):
    output = [ m for m in matches if m.end_point.timestamp > destination_min_date ]
    return output
