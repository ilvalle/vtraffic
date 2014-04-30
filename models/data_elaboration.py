import operator
MODE_STEP=5
#import time
def __get_rows(query, use_cache=True, limitby=None):
	def __get_rows_local(query):
		query_1 = query & ((end.gathered_on.epoch() - start.gathered_on.epoch()) < 1800)
		#t0 = time.time()
		#rows = db( query ).select(start.ALL, end.ALL,
		#                          orderby=start.gathered_on,
		#                          left=start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on)),
		#                          limitby=limitby,
		#                          cacheable = True)
		#print 'LEN initial rows', len(rows)
		#matches2 = [r for r in rows if (r.end_point.gathered_on - r.start_point.gathered_on < datetime.timedelta(minutes=30)) ]
		#t1 = time.time()
		matches = db( query_1 ).select(start.ALL, end.ALL,
		                          orderby=start.gathered_on,
		                          left=start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on)),
		                          limitby=limitby,
		                          cacheable = True)
		#t2 = time.time()

		#print 'LEN initial rows', len(matches), len(matches2), '\t %s - %s' % (t1-t0, t2-t1)
		#if rows:
	    #	print '\t', matches[0] , matches2[0]

		matches = __remove_dup(matches)	# Remove matches based on the same timestamp

		# Compute the elapsed_time 	
		for m in matches:
			m.start_point.epoch = EPOCH_M(m[start.gathered_on])
			m.end_point.epoch   = EPOCH_M(m[end.gathered_on])
			m.elapsed_time      = m.end_point.epoch - m.start_point.epoch
	
		matches = __filter_twins(matches) # Remove matches with the same elapsed_time at the same time
		return matches
	if use_cache:
		key = 'rows_%s' % query
		if len(key)>200:
			key = 'rows_%s' % md5_hash(key)
		matches = cache.ram( key, lambda: __get_rows_local(query), time_expire=CACHE_TIME_EXPIRE)
	else: 
		matches	= __get_rows_local(query)
	#__save_match(matches)
	return matches

### issue 1
# station_id mac datetime
# 1          'a' 12:00
# 2          'a' 14:00
# 1          'a' 12:30
# 2          'a' 14:30
# The output of the leftjoin is
# station_id_start mac datetime_start station_id_end datetime_end
# 1                'a' 12:00          2              12:30 
# 1                'a' 12:00          2              14:30   <<-- this is not correct
# 2                'a' 14:00          2              14:30

### issue 2
# station_id mac datetime
# 1          'a' 12:00
# 1          'a' 12:30
# 2          'a' 14:30
# The output of the leftjoin is
# station_id_start mac datetime_start station_id_end datetime_end
# 1                'a' 12:00          2              14:30 <<-- this is not correct
# 1                'a' 12:30          2              14:30   

### issue 3
# station_id mac datetime
# 1          'a' 12:00
# 2          'a' 12:30
# 2          'a' 14:30
# The output of the leftjoin is
# station_id_start mac datetime_start station_id_end datetime_end
# 1                'a' 12:00          2              12:30 
# 1                'a' 12:00          2              14:30 <<-- this is not correct  

def __remove_dup(rows):
	hash_end = {}
	hash_start = {}
	remove=[]
	for pos, r in enumerate(rows):
		if r.start_point.id in hash_start:
			pos_prev = hash_start[r.start_point.id]
			prev = rows[pos_prev]
			if (r.end_point.gathered_on < prev.end_point.gathered_on):
				remove.append(pos_prev)			# remove the old one
				hash_start[r.start_point.id] = pos	# update the pos to the new one
			else:
				remove.append(pos)			# remove the current one
		else:
			hash_start[r.start_point.id] = pos			
		if r.end_point.id in hash_end:
			pos_prev = hash_end[r.end_point.id]
			prev = rows[pos_prev]
			if (r.start_point.gathered_on > prev.start_point.gathered_on):
				remove.append(pos_prev)			# remove the old one
				hash_end[r.end_point.id] = pos		# update the pos to the new one
			else:
				remove.append(pos)			# remove the current one
		else:
			hash_end[r.end_point.id] = pos

	rows = [r for pos, r in enumerate(rows) if pos not in remove]
	return rows

# Remove matches with the same elapsed_time computed at the same time (issue: vehicle with more than one device onboard)
def __filter_twins(rows):
	out = []
	for pos, row in enumerate(rows):
		next = rows[pos + 1 ] if pos != len(rows) -1 else None
		if not (next) or row.start_point.epoch != next.start_point.epoch or row.elapsed_time != next.elapsed_time:
			out.append(row)
	return rows

# Query the matches and create a list of blocks, one block for each time_frame
def __get_blocks_scheduler (query, block_seconds, reset_cache=False):
	def __get_blocks_local(query, block_seconds):
		matches = db(query).select(cacheable=False, orderby=db.match.epoch_orig)
		blocks  = __split_matches2time_frame( matches, block_seconds)
		return blocks
	key = 'blocks_%s%s' % (query, block_seconds)
	if len(key)>200:
		key = 'blocks_%s' % md5_hash(key)
	blocks = cache.ram( key, lambda: __get_blocks_local(query, block_seconds), time_expire= 0 if reset_cache else 900)
	return blocks

# Return matches grouped to the specific time_frame they belong to 
def __split_matches2time_frame(matches, time_frame_size):
	l = []	
	f = lambda row: row.epoch_orig // time_frame_size
	for key, group in groupby(matches, f):
		ll = list(group)
		l.append( ll ) 
	return l

# Return matches grouped to the specific time_frame they belong to 
# if the gap between two matches is higher time_frame_size * 2, the put a 0 (useful for plotting chart)
def __split2time_frame2(matches, time_frame_size):
	l = [] 
	if len(matches) == 0: return l
	first=True
	prev = matches[0]

	for match in matches:
		if not first and (match.gathered_on < limit):
			l[len(l)-1].append(match)
		elif (prev.gathered_on + (datetime.timedelta(seconds=time_frame_size) * 2)) < match.gathered_on:
			l.append([prev])
			l.append([match])
		else:
			limit = match.gathered_on + datetime.timedelta(seconds=time_frame_size)
			l[len(l):] = [[match]]
			first = False
		prev = match
	
	return l


# return the mode along a list of rows (block)
def __mode(block, block_seconds=0, vertical_block_seconds=0):
	block = sorted(block, key=operator.itemgetter('elapsed_time'))
	initial_time_frame = block[0]['elapsed_time']
	end_time_frame     = block[-1]['elapsed_time']
	mode_value = {'counter':0, 'seconds':0}
	i = 0
	for second in range(0,end_time_frame-initial_time_frame, MODE_STEP):
		current_initial = initial_time_frame + second
		current_end     = current_initial + vertical_block_seconds
		counter = 0
		while i < len(block):
			ele = block[i]
			if current_initial <= ele['elapsed_time'] < current_end:
				counter = counter + 1 
			elif current_end < ele['elapsed_time']:
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


# This skeleton allows to run easily statistical analysis across rows splitted into frames
def __wrapper_elaboration( blocks_list, 
                           function, 
                           block_seconds=800, 
                           vertical_block_seconds=30, 
                           compare=False):	
	if compare:
		first_date = blocks_list[0][0][db.match.gathered_on_orig]
		day = datetime.datetime(first_date.date().year, first_date.date().month, first_date.date().day)
		reference_seconds = EPOCH_M(day)
	else:
		reference_seconds = 0
	output = []
	prev   = None
	for block in blocks_list:
		if len(block) <= 2:		# two values are not enough, lets pass
			continue
		current = block[0]
		seconds = block[0].epoch_orig - (block[0].epoch_orig % block_seconds) - reference_seconds
		if prev and current.epoch_orig > prev.epoch_orig + (block_seconds*3):	#fill the gap with three empty values
			output.append ( [ (prev_seconds + block_seconds + block_seconds/2) * 1000,	0] )
			output.append ( [ (seconds - block_seconds/2) * 1000,	0] )
		value = function(block, block_seconds, vertical_block_seconds)
		output.append ( [(seconds + block_seconds/2) * 1000, value * 1000] )
		prev, prev_seconds = current, seconds
	return output
	
	
def __compute_mode( query, block_seconds=800, vertical_block_seconds=30, compare=False, use_cache=True):
    blocks_list = __get_blocks_scheduler (query, block_seconds, reset_cache=False)
    if (len(blocks_list) == 0):
        return  {'data': [],'label':'No matches', 'id':'mode_%s' %  block_seconds }

    key = 'mode_%s%s%s%s' % (block_seconds, vertical_block_seconds, compare, query)
    if len(key)>200:
        key = 'mode_%s' % md5_hash(key)

    # Cache the mode for each day, so we need to compute only the last day
    data = cache.ram( key, lambda: __wrapper_elaboration( blocks_list,
                                                          __mode,
                                                          block_seconds, 
                                                          vertical_block_seconds=vertical_block_seconds, 
                                                          compare=compare),  
                      time_expire=CACHE_TIME_EXPIRE)
    if compare:
        fdate = blocks_list[0][0][db.match.gathered_on_orig]
        label = fdate.strftime('%a %d, %b' )
    else:
        label = "Mode (%ss)" % block_seconds
    return {'data': data,'label':label, 'id':'mode_%s' %  block_seconds }

