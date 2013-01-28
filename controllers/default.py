# -*- coding: utf-8 -*-

from datetime import timedelta
import datetime, time

start = db.record.with_alias('start_point')
end = db.record.with_alias('end_point')

if request.function != 'wiki':	# temp fix due to double menu
	from gluon.tools import Wiki
	response.menu += Wiki(auth).menu(controller="default", function="wiki")

def index():
	#return response.render('default/wiki.html', auth.wiki())
	redirect(URL(f='wiki', args=['about']))

def wiki():
	return auth.wiki(render='html')

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
		redirect(URL(f='index', vars={'id':form.vars.station_id}))
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

def compare():
	content = auth.wiki(slug='compare', render='html')
	return response.render('default/compare.html', {'content':content})

@cache(request.env.path_info + (request.vars.diff_temp or ''), time_expire=None, cache_model=cache.ram)
def get_lines():
	session.forget(response)
	line_type = request.vars.type or 'median'
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 900
	except:	block_seconds = 900
	day = start.gathered_on.year() | start.gathered_on.month() | start.gathered_on.day()  
	# Gets the days with data 
	days = db( (start.station_id == 13)  ).select(
						start.gathered_on.year(), 
						start.gathered_on.month(), 
						start.gathered_on.day(),
						groupby=day,
						cache=(cache.ram, 3600),
						cacheable = True)	
	out={}
	# make the median day by day
	print days
	for d in days:
		year, month, day  = d[start.gathered_on.year()], d[start.gathered_on.month()], d[start.gathered_on.day()]

		query = ((start.gathered_on.year() == year) &
			 (start.gathered_on.month() == month) &
			 (start.gathered_on.day() == day) &
			 (end.gathered_on.year() == year) &
			 (end.gathered_on.month() == month) &
			 (end.gathered_on.day() == day) &
			 (start.station_id == 13) &
			 (end.station_id == 14))

		rows_pos = __get_rows(query)
		
		if line_type == 'lower':
			out = __get_lower_rows(rows_pos, block_seconds )
		else:
			dd = __get_median_rows(rows_pos, block_seconds, test=True)
			dd['id'] = dd['id'] + '%s' % day
			out['%s' % dd['id']]=dd
		
	return response.render('generic.json', out)

def origin_destination():
	session.forget(response)
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
	except:	block_seconds = 900
	id_start = 13
	id_end = 14
	
	rows = __get_rows_stations (id_start, id_end)
	n_start = db(db.record.station_id == id_start).count( cache=(cache.ram, 3600))
	n_end = db(db.record.station_id == id_end).count( cache=(cache.ram, 3600))

	info = {'n': len(rows), 'n_start':n_start, 'n_end':n_end}
	return response.render('default/diff.html', {'info':info})

@cache(request.env.path_info,time_expire=None,cache_model=cache.ram)
def get_diff():
	session.forget(response)
	id_start = 13
	id_end = 14

	rows = __get_rows_stations (id_start, id_end)
	
	logs=[]
	for row in rows:
		t = row.end_point.gathered_on - row.start_point.gathered_on
		logs.append( [ (row[start.gathered_on.epoch()]+3600) * 1000,
				       int(t.total_seconds()) * 1000 ]	)
	all_logs = {'logs':{'data':logs, 'label': 'matches', 'id':'logs'}}	

	for seconds in xrange(900, 1000, 100):
		out = __get_lower_rows(rows, seconds )
		all_logs[out['id']] = out
	
	for seconds in xrange(900, 1000, 100):
		out_m = __get_median_rows(rows, seconds)
		all_logs[out_m['id']] = out_m

	# single trends
	hours = __get_trend(id_start, 3600)
	#tens = __get_trend(id_start, 600)
	fifteens = __get_trend(id_start, 900)
	all_logs['trendstart_h'] = {'data':hours, 'label': 'trend start h', 'id':'trendstart_h', 'yaxis': 2 }
	#all_logs['trendstart_10'] = {'data':tens, 'label': 'trend start 10m', 'id':'trendstart_10', 'yaxis': 2 }
	all_logs['trendstart_15'] = {'data':fifteens, 'label': 'trend start 15m', 'id':'trendstart_15', 'yaxis': 2 }

	hours = __get_trend(id_end, 3600)
	#tens = __get_trend(id_end, 600)
	fifteens = __get_trend(id_end, 900)
	all_logs['trendend_h'] = {'data':hours, 'label': 'trend end h', 'id':'trendend_h', 'yaxis': 2 }
	#all_logs['trendend_10'] = {'data':tens, 'label': 'trend end 10m', 'id':'trendend_10', 'yaxis': 2 }
	all_logs['trendend_15'] = {'data':fifteens, 'label': 'trend end 15m', 'id':'trendend_15', 'yaxis': 2 }

	return response.render('generic.json', all_logs)

# external request, might be ajax too
def get_line():
	session.forget(response)
	id_start = 13
	id_end = 14
	line_type = request.vars.type
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
	except:	block_seconds = 500

	if line_type == 'median':
		out = __get_median(id_start, id_end, block_seconds)
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
	rows = db( query ).select(start.ALL, 
		          end.ALL, 
			  start.gathered_on.epoch(),
			  end.gathered_on.epoch(),
			  orderby=start.gathered_on.epoch(),
			  left=start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on)),
			  cache=(cache.ram, 3600),
			  cacheable = True)
	matches = [r for r in rows if (r.end_point.gathered_on - r.start_point.gathered_on < datetime.timedelta(days=1)) ]
	matches = __remove_dup(matches)
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

	out = [ [ (block[0][db.record.gathered_on.epoch()]+3600 + block_seconds/2) * 1000, len(block) ] for block in l]
	return out

def __get_lower( id_start, id_end, block_seconds ):
	rows = __get_rows_stations (id_start, id_end)
	return __get_lower_rows(rows, block_seconds)

def __get_median( id_start, id_end, block_seconds=800, vertical_block_seconds=30 ):
	rows = __get_rows_stations (id_start, id_end)
	return __get_median_rows(rows, block_seconds, vertical_block_seconds, False)

def __get_lower_rows( rows, block_seconds, test=False ):
	l = []
	first=True
	prev = rows[0]
	for r in rows:
		if not first and r.start_point.gathered_on < limit:
			l[len(l)-1].append(r)
		elif (prev.start_point.gathered_on + (datetime.timedelta(seconds=block_seconds) * 2)) < r.start_point.gathered_on:
			l.append([0, prev])
			l.append([0, r])
		else:
			limit = r.start_point.gathered_on + datetime.timedelta(seconds=block_seconds)
			l[len(l):] = [[r]]
			first = False
		prev = r

	lower_bound=[]
	for block in l:
		if block[0] == 0:
			lower_bound.append ( [(block[1][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
						0] )
		elif len(block) >= 1 and len(block) <= 2:
			pass
			#lower_bound.append ( [(block[0][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,0] )
		else:		
			cur_min=min([(r.end_point.gathered_on - r.start_point.gathered_on) if r != 0 else 0 for r in block ])	
			lower_bound.append ( [(block[0][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
				int(cur_min.total_seconds()) * 1000] )
	
	return {'data': lower_bound,'label':"Lower bound (%ss)" % block_seconds, 'id':'lower_bound_%s' %  block_seconds };

def __get_median_rows( rows, block_seconds=800, vertical_block_seconds=30, test=False):
	l = [] 
	first=True
	prev = rows[0]
	for r in rows:
		if not first and r.start_point.gathered_on < limit:
			l[len(l)-1].append(r)
		elif (prev.start_point.gathered_on + (datetime.timedelta(seconds=block_seconds) * 2)) < r.start_point.gathered_on:
			l.append([0, prev])
			l.append([0, r])
		else:
			limit = r.start_point.gathered_on + datetime.timedelta(seconds=block_seconds)
			l[len(l):] = [[r]]
			first = False
		prev = r

	median=[]
	fdate = l[0][0][start.gathered_on]
	day = datetime.datetime(fdate.date().year, fdate.date().month, fdate.date().day)
	for block in l:
		if block[0] == 0:
			if test:
				mdate = block[1][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[1][start.gathered_on.epoch()]+3600
			median.append ( [ (seconds  + block_seconds/2) * 1000,	0] )
		else:
			# compute the horizontal seconds
			if test:
				mdate = block[0][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[0][start.gathered_on.epoch()]+3600

			if len(block) >= 1 and len(block) <= 2:
				# pass instead of plotting real value, otherwise it will draw odd valuea 
				pass
				#median.append ( [ (seconds  + block_seconds/2) * 1000,	0] )
			else:
				initial_time_frame = min([(r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
				end_time_frame = max( [ (r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
				n_windows = (end_time_frame - initial_time_frame) / vertical_block_seconds		
				windows = [0] * (n_windows + 1)
				values = ''
				for ele in block:
					diff = (ele[end.gathered_on.epoch()] - ele[start.gathered_on.epoch()])
					cur_pos = (diff - initial_time_frame)  / vertical_block_seconds
					windows[cur_pos] += 1

				tot = initial_time_frame + (vertical_block_seconds * windows.index(max(windows)))
				median.append ( [(seconds + block_seconds/2) * 1000,
						 (tot + (vertical_block_seconds/2))  * 1000] )
	if test:
		label = fdate.strftime('%a %d, %b' )
		#label += " [M(%(name)s)]" % {'name':block_seconds}
	else:
		label = "Median (%ss)" % block_seconds
	return {'data': median,'label':label, 'id':'median_%s' %  block_seconds };

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
