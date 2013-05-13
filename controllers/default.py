# -*- coding: utf-8 -*-
from applications.vtraffic.modules.tools import EPOCH_M
from datetime import timedelta
from gluon.utils import md5_hash
from itertools import groupby
import datetime, time
import operator

start = db.record.with_alias('start_point')
end = db.record.with_alias('end_point')
CACHE_TIME_EXPIRE=10
MODE_STEP=5

# temp fix due to double menu
zero = request.args(0) or 'index'
if request.function != 'wiki' and zero and not(zero.isdigit()):
	from gluon.tools import Wiki
	response.menu += Wiki(auth).menu(controller="default", function="wiki")

def index():
	#return response.render('default/wiki.html', auth.wiki())
	redirect(URL(f='wiki', args=['about']))

def wiki():
	wiki = auth.wiki(render='html')
	if isinstance (wiki, dict) and 'title' in wiki:
		response.page_title += " - %s" % wiki['title']
	return wiki

@auth.requires_login()
def add_log():
	import re
	from datetime import datetime
	from gluon.tools import Crud
	pattern = re.compile(r"""
			\[(?P<time>.*?)\]
			\s(?P<mac>[0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2})
			\s(?P<more>.*)
			\s*"""
			, re.VERBOSE)
	crud = Crud(db)
	form = crud.create(db.log)
	if form.process(dbio=False).accepted:
		form.vars.log_id = db.log.insert(**dict(form.vars))
		request.vars.log_file.file.seek(0)
		count=0
		for line in request.vars.log_file.file:
			#print 'l', line
			match = pattern.findall(line)	
			if match:
				d = datetime.strptime(match[0][0], '%m/%d/%y %H:%M:%S')
				db.record.insert(log_id=form.vars.log_id, 
						station_id=form.vars.station_id,
						mac=match[0][1], 
						gathered_on=d)			
				count += 1
		session.flash = 'Inserted %s record' % count
		try:
			cache.memcache.flush_all()	#memcache client
		except:
			cache.memcache.clear() 		#web2py ram client 

		redirect(URL(c='plot', f='index', vars={'id':form.vars.station_id}))
	return response.render('default/index.html', dict(form=form))

@auth.requires_login()
def add_station():
	from gluon.tools import Crud
	crud = Crud(db)
	form = crud.create(db.station)
	if form.process(dbio=True).accepted:
		session.flash = 'Station added correctly'
		redirect(URL(f='index'))
	return response.render('default/index.html', dict(form=form))

id_origin = int(request.vars.id_origin) if request.vars.id_origin and request.vars.id_origin.isdigit() else 13
id_destination  = int(request.vars.id_destination) if request.vars.id_destination and request.vars.id_destination.isdigit() else 14
time_frame_size = int(request.vars.diff_temp) if request.vars.diff_temp and request.vars.id_destination.isdigit() else 900

@cache(request.env.path_info + '%s-%s-%s' % (id_origin, id_destination, time_frame_size) , time_expire=None, cache_model=cache.ram)
def compare_series():
	session.forget(response)
	
	day = start.gathered_on.year() | start.gathered_on.month() | start.gathered_on.day()  
	# Gets the days with data 
	days = db( (start.station_id == id_origin)  ).select(
						start.gathered_on.year(), 
						start.gathered_on.month(), 
						start.gathered_on.day(),
						groupby=day,
						orderby=day,
						cacheable = True)	
	out=[]
	# make the mode day by day
	for d in days:
		year, month, day  = d[start.gathered_on.year()], d[start.gathered_on.month()], d[start.gathered_on.day()]

		query = ((start.gathered_on.year() == year) &
			 (start.gathered_on.month() == month) &
			 (start.gathered_on.day() == day) &
			 (end.gathered_on.year() == year) &
			 (end.gathered_on.month() == month) &
			 (end.gathered_on.day() == day) &
			 (start.station_id == id_origin) &
			 (end.station_id == id_destination))

		data = __compute_mode(query, time_frame_size, 30, compare=True)
		if len(data['data']) != 0:
			data['id'] = data['id'] + '%s%s%s' % (year,month,day)
			out.append(data)

	return response.render('generic.json', {'series':out})

#@cache(request.env.path_info + '%s-%s' % (id_origin, id_destination), time_expire=None, cache_model=cache.ram)
def get_series():
	session.forget(response)

	rows = __get_rows_stations (id_origin,  id_destination)
	query = (start.station_id == id_origin) & (end.station_id == id_destination)
	logs=[]
	for row in rows:
		logs.append( [ row.start_point['epoch'] * 1000, row['elapsed_time'] * 1000 ]	)

	all_logs = []
	all_logs.append( {'data':logs, 'label': 'matches', 'id':'logs'} )

	for seconds in xrange(900, 1000, 100):
		all_logs.append( __compute_lower(query, seconds ) )
	
	for seconds in xrange(900, 1000, 100):
		all_logs.append( __compute_mode(query, seconds) )
		#all_logs.append( __get_mode_rows(rows, seconds) )

	# single trends
	hours = __get_trend(id_origin, 3600)
	#tens = __get_trend(id_start, 600)
	fifteens = __get_trend(id_origin, 900)
	all_logs.append( {'data':hours, 'label': 'trend start h', 'id':'trendstart_h', 'yaxis': 2, 'bars':{'show':'true', 'fill': 'true', 'align':'center', 'barWidth': 60*60*1000}, 'lines': {'show':'false'}} )
	#all_logs['trendstart_10'] = {'data':tens, 'label': 'trend start 10m', 'id':'trendstart_10', 'yaxis': 2 }
	all_logs.append( {'data':fifteens, 'label': 'trend start 15m', 'id':'trendstart_15', 'yaxis': 2 } )

	hours = __get_trend(id_destination, 3600)
	#tens = __get_trend(id_end, 600)
	fifteens = __get_trend(id_destination, 900)
	all_logs.append( {'data':hours, 'label': 'trend end h', 'id':'trendend_h', 'yaxis': 2 } )
	#all_logs['trendend_10'] = {'data':tens, 'label': 'trend end 10m', 'id':'trendend_10', 'yaxis': 2 }
	all_logs.append( {'data':fifteens, 'label': 'trend end 15m', 'id':'trendend_15', 'yaxis': 2 } )

	return response.render('generic.json', {'series':all_logs})

# external request, might be ajax too
def get_line():
	session.forget(response)
	id_start = id_origin
	id_end = id_destination
	line_type = request.vars.type
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
	except:	block_seconds = 500

	if line_type == 'mode':
		out = __get_mode(id_start, id_end, block_seconds)
	elif line_type == 'lower':
		out = __get_lower( id_start, id_end, block_seconds )
	elif line_type == 'trendstart':
		out = {'data':__get_trend( id_start, block_seconds ), 'label': 'trend start %ss' % block_seconds , 'id':'trendstart_%s' % block_seconds , 'yaxis': 2 }
	elif line_type == 'trendend':
		out = {'data':__get_trend( id_end, block_seconds ), 'label': 'trend end %ss' % block_seconds , 'id':'trendend_%s' % block_seconds , 'yaxis': 2 }
	else:
		return 'errore'
	out = {out['id']:out}

	return response.render('generic.json', out)

def __get_rows_stations(station_id_start, station_id_end):
	query = (start.station_id == station_id_start) & (end.station_id == station_id_end)
	return __get_rows(query)


def __get_rows(query):
	def __get_rows_local(query):
		rows = db( query ).select(start.ALL, end.ALL, 
								  orderby=start.gathered_on,
								  left=start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on)),
								  cacheable = True)
		matches = [r for r in rows if (r.end_point.gathered_on - r.start_point.gathered_on < datetime.timedelta(minutes=30)) ]
		matches = __remove_dup(matches)	# Remove matches based on the same timestamp
		# Compute the elapsed_time 	
		for m in matches:
			m.start_point.epoch = EPOCH_M(m[start.gathered_on])
			m.end_point.epoch   = EPOCH_M(m[end.gathered_on])
			m.elapsed_time      = m.end_point.epoch - m.start_point.epoch
	
		matches = __filter_twins(matches) # Remove matches with the same elapsed_time at the same time
		return matches
	key = 'rows_%s' % query
	if len(key)>200:
		key = 'rows_%s' % md5_hash(key)
	matches = cache.ram( key, lambda: __get_rows_local(query), time_expire=CACHE_TIME_EXPIRE)
	return matches

def __get_blocks(query, block_seconds):
	def __get_blocks_local(query, block_seconds):
		rows   = __get_rows(query)
		blocks = __split2time_frame(rows, block_seconds)
		return blocks
	key = 'blocks_%s%s' % (query, block_seconds)
	if len(key)>200:
		key = 'blocks_%s' % md5_hash(key)
	blocks = cache.ram( key, lambda: __get_blocks_local(query, block_seconds), time_expire=CACHE_TIME_EXPIRE)
	return blocks

	
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

def __get_trend(station_id, block_seconds):
	query = db.record.station_id == station_id
	rows = db(query).select(db.record.gathered_on, 
							db.record.gathered_on.epoch(),
							orderby=db.record.gathered_on.epoch(),
							cache=(cache.ram, 3600),
			        		cacheable=True )
	#print '__get_trend(%s, %s)' % (station_id, block_seconds), len(rows)
	l = []
	first = True
	last = 	rows[0]
	for r in rows:
		if not first and r[db.record.gathered_on] < limit:
			l[len(l)-1].append(r)

		elif (last[db.record.gathered_on] + (datetime.timedelta(seconds=block_seconds) * 2)) < r[db.record.gathered_on]:
			l.append([last])
			l.append([r])
		else:
			limit = r[db.record.gathered_on] + datetime.timedelta(seconds=block_seconds)
			l.append([r])
			first = False
		last = 	r

	out = [ [ ( EPOCH_M (block[0][db.record.gathered_on]) + block_seconds/2) * 1000, len(block) ] for block in l]
	return out

def __get_lower( id_start, id_end, block_seconds ):
	rows = __get_rows_stations (id_start, id_end)
	return __get_lower_rows(rows, block_seconds)

def __get_mode( id_start, id_end, block_seconds=800, vertical_block_seconds=30 ):
	query = (start.station_id == id_start) & (end.station_id ==  id_end)
	data = __compute_mode( query, block_seconds=block_seconds, vertical_block_seconds=vertical_block_seconds, compare=False)
	return data

def __compute_lower( query, block_seconds, compare=False ):
	blocks_list = __get_blocks (query, block_seconds)
	data = []	
	if (len(blocks_list) != 0):
		data = __compute_wrapper( blocks_list,
                                  __lower,
                                  block_seconds, 
                                  compare=compare)
	return {'data': data,'label':"Lower bound (%ss)" % block_seconds, 'id':'lower_bound_%s' %  block_seconds };

def __compute_mode( query, block_seconds=800, vertical_block_seconds=30, compare=False):
	blocks_list = __get_blocks (query, block_seconds)
	if (len(blocks_list) == 0):
		return  {'data': [],'label':'No matches', 'id':'mode_%s' %  block_seconds }

	key = 'mode_%s%s%s%s' % (block_seconds, vertical_block_seconds, compare, query)
	if len(key)>200:
		key = 'mode_%s' % md5_hash(key)
	# Cache the mode for each day, so we need to compute only the last day
	data = cache.ram( key, lambda: __compute_wrapper(blocks_list,
                                                     __mode,
                                                     block_seconds, 
                                                     vertical_block_seconds=vertical_block_seconds, 
                                                     compare=compare),  
                      time_expire=CACHE_TIME_EXPIRE)
	if compare:
		fdate = rows[0][start.gathered_on]
		label = fdate.strftime('%a %d, %b' )
	else:
		label = "Mode (%ss)" % block_seconds
	return {'data': data,'label':label, 'id':'mode_%s' %  block_seconds }

# Return matches grouped to the specific time_frame they belong to 
def __split2time_frame(matches, time_frame_size):	
	l = []	
	for key, group in groupby(matches, lambda row: row.start_point.epoch // time_frame_size):
		ll = list(group)
		l.append( ll ) 
	return l

# Return matches grouped to the specific time_frame they belong to 
# if the gap between two matches is higher time_frame_size * 2, the put a 0 (useful for plotting chart)
def __split2time_frame2(matches, time_frame_size):
	l = [] 
	first=True
	prev = matches[0]

	for match in matches:
		if not first and (match.start_point.epoch < limit):
			l[len(l)-1].append(match)
		elif (prev.start_point.epoch + time_frame_size * 2) < match.start_point.epoch:
			l.append([0, prev])
			l.append([0, match])
		else:
			limit = match.start_point.epoch + time_frame_size
			l[len(l):] = [[match]]
			first = False
		prev = match
	
	return l

### Functions
# return the mode along a list of rows (block)
def __mode(block, block_seconds, vertical_block_seconds):
	block = sorted(block, key=operator.itemgetter('elapsed_time'))
	initial_time_frame = block[0].elapsed_time
	end_time_frame     = block[len(block)-1].elapsed_time
	mode_value = {'counter':0, 'seconds':0}
	for second in range(0,end_time_frame-initial_time_frame, MODE_STEP):
		current_initial = initial_time_frame + second
		current_end     = current_initial + vertical_block_seconds
		counter = 0
		for ele in block:
			if current_initial <= ele.elapsed_time < current_end:
				counter = counter + 1 
			elif current_end < ele.elapsed_time:
				break
			if counter > mode_value['counter']:
				mode_value['counter'] = counter
				mode_value['seconds'] = current_initial
	return mode_value['seconds'] + (vertical_block_seconds/2)

# return the min elapsed_time across the current block of rows
def __lower(block, block_seconds, vertical_block_seconds):
	value = min([ row['elapsed_time'] if row != 0 else 0 for row in block ])
	return value

# return the number of matches for each block given as input
def __trend(block, block_seconds, vertical_block_seconds):
	value = len(block)
	return value

# This skeleton allows to run easily statistical analysis across rows splitted into frames
def __compute_wrapper( blocks_list, 
                       function, 
                       block_seconds=800, 
                       vertical_block_seconds=30, 
                       compare=False):	
	if compare:
		first_date = blocks_list[0][0][start.gathered_on]
		day = datetime.datetime(first_date.date().year, first_date.date().month, first_date.date().day)
		reference_seconds = EPOCH_M(day)
	else:
		reference_seconds = 0
	output=[]
	for block in blocks_list:
		if block[0] == 0:
			seconds = block[1].start_point.epoch - reference_seconds
			output.append ( [ (seconds + block_seconds/2) * 1000,	0] )
		elif len(block) <= 2:		# two values are not enough, lets pass
			pass
		else:
			seconds = block[0].start_point.epoch - (block[0].start_point.epoch % block_seconds) - reference_seconds
			value = function(block, block_seconds, vertical_block_seconds)
			output.append ( [(seconds + block_seconds/2) * 1000, value * 1000] )
	return output

def user():
    return dict(form=auth())

@auth.requires_login()
def download():
    return response.download(request, db)

@auth.requires_signature()
def data():
    return dict(form=crud())

#def saveDb():
#    return db.export_to_csv_file(open(request.folder+'/backup.csv', 'wb'))
#
#def restoreDb():
#    db.import_from_csv_file(open(request.folder+'backup.csv', 'rb'))
