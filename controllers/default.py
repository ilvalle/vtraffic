# -*- coding: utf-8 -*-


import re
from datetime import timedelta
import datetime, time

start = db.record.with_alias('start_point')
end = db.record.with_alias('end_point')

def index():
	#return response.render('default/wiki.html', auth.wiki())
	redirect(URL(f='compare'))

@auth.requires_login()
def add_log():
	from datetime import datetime
	pattern = re.compile(r"""
			\[(?P<time>.*?)\]
#			\s(?P<mac>[0-9A-F]{2}[:]{5}[0-9A-F]{2})?)
			\s(?P<mac>[0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2}[:][0-9A-F]{2})
			\s(?P<more>.*)
			\s*"""
			, re.VERBOSE)

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
		redirect(URL(f='read', vars={'id':form.vars.station_id}))
	return response.render('default/index.html', dict(form=form))

@auth.requires_login()
def add_station():
	form = crud.create(db.station)
	if form.process(dbio=True).accepted:
		session.flash = 'Station insert correctly'
		redirect(URL(f='index'))
	return response.render('default/index.html', dict(form=form))

#def insert():
#	file_stream = open("/home/pvalleri/Desktop/test/bluelog.log", "r")
#	matches=[]
#	for line in file_stream:
#		match = pattern.findall(line)	
#		if match:
#			d = datetime.strptime(match[0][0], '%m/%d/%y %H:%M:%S')
#			db.record.insert(mac=match[0][1], gathered_on=d)	
#	return 'done'
	
def read():
	try:	query = db.record.station_id == int(request.vars.id)
	except: 
		request.flash= 'ID not valid'
		return 'error'
	rows = db(query).select(db.record.gathered_on, db.record.gathered_on.epoch())
	info = {'n': len(rows), 'start': rows[0].record.gathered_on, 'end': 'vuoto'}
	return dict(info=info)

def compare():
	return response.render('default/compare.html', {})

def get_lines():
	line_type = request.vars.type or 'median'
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 900
	except:	block_seconds = 900
	start = db.record.with_alias('start_point')
	end = db.record.with_alias('end_point')
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

		rows = db( query ).select(
				   start.gathered_on,start.mac,start.id,
				   end.gathered_on, end.mac, end.id,
				   start.gathered_on.epoch(),
				   end.gathered_on.epoch(),
				   orderby=start.gathered_on.epoch(),
				   left= start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on) ),
				   cache=(cache.ram, 3600),
				   cacheable = True)
		rows_pos = [r for r in rows if (r.end_point.gathered_on - r.start_point.gathered_on < datetime.timedelta(seconds=12000))]
		#print month, day, 'N: ', len(rows) 
		if line_type == 'lower':
			out = __get_lower_rows(rows_pos, block_seconds )
		else:
			dd = __get_median_rows(rows_pos, block_seconds, test=True)
			dd['id'] = dd['id'] + '%s' % day
			out['%s' % dd['id']]=dd
		
	return response.render('generic.json', out)

def origin_destination():
	try: block_seconds = int(request.vars.diff_temp) if request.vars.diff_temp else 500
	except:	block_seconds = 900
	id_start = 13
	id_end = 14
	
	rows = __get_rows (id_start, id_end)
	n_start = db(db.record.station_id == id_start).count( cache=(cache.ram, 3600))
	n_end = db(db.record.station_id == id_end).count( cache=(cache.ram, 3600))

	info = {'n': len(rows), 'n_start':n_start, 'n_end':n_end}

	return response.render('default/diff.html', {'info':info})

#def get_hour():
#	c = db.record.id.count()
#	s = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour() 
#	#dd = db.record.gathered_on.timedelta(minutes=30) 
#	rows = db(db.record.id > 0).select(db.record.gathered_on.epoch(), c, groupby=s)
#
#	data = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows]
#
#	return response.render('generic.json', dict(data=data))
#
#def get_minute():
#	c = db.record.id.count()
#	s = db.record.gathered_on.year() | db.record.gathered_on.month() | db.record.gathered_on.day() | db.record.gathered_on.hour() | db.record.gathered_on.minutes()
#
#	rows = db(db.record.id > 0).select(db.record.gathered_on.epoch(), c, groupby=s)
#
#	data = [ [ (r[db.record.gathered_on.epoch()] +3600)* 1000, r[c] ] for r in rows]
#	return response.render('generic.json', dict(data=data))

def get_diff():
	id_start = 13
	id_end = 14

	rows = __get_rows (id_start, id_end)

					
	logs=[]
	for pos, r in enumerate(rows):
		t = r.end_point.gathered_on - r.start_point.gathered_on
		logs.append( [ (r[start.gathered_on.epoch()]+3600) * 1000,
				       int(t.total_seconds()) * 1000 ]	)
	all_logs = dict(logs={'data':logs, 'label': 'matches', 'id':'logs'})	

	for seconds in xrange(700, 1000, 100):
		out = __get_lower_rows(rows, seconds )
		all_logs[out['id']] = out
	
	for seconds in xrange(700, 1000, 100):
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


def __get_trend(station_id, block_seconds):
	query = db.record.station_id == station_id
	rows = db(query).select(
						db.record.gathered_on, 
						db.record.gathered_on.epoch(),
						orderby=db.record.gathered_on.epoch(),
						cache=(cache.ram, 3600),
			        	cacheable=True )
	#print '__get_trend(%s, %s)' % (station_id, block_seconds), len(rows)
	l = []
	first = True
	last = 	rows[0]
	for pos, r in enumerate(rows):
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
	rows = __get_rows (id_start, id_end)
	return __get_lower_rows(rows, block_seconds)

def __get_median( id_start, id_end, block_seconds=800, vertical_block_seconds=20 ):
	rows = __get_rows (id_start, id_end)
	return __get_median_rows(rows, block_seconds, vertical_block_seconds, False)

def __get_rows(station_id_start, station_id_end):
	rows = db( (start.station_id == station_id_start) &
		       (end.station_id == station_id_end)
		     ).select(start.ALL, 
			          end.ALL, 
					  start.gathered_on.epoch(),
					  end.gathered_on.epoch(),
					  orderby=start.gathered_on.epoch(),
					  left= start.on( (start.mac == end.mac) & (start.gathered_on < end.gathered_on)),
					  cache=(cache.ram, 3600),
					  cacheable = True)
	rows_pos = [r for r in rows if (r.end_point.gathered_on - r.start_point.gathered_on < datetime.timedelta(seconds=12000)) ]
	return rows_pos

def __get_lower_rows( rows, block_seconds ):
	l = []
	first=True
	prev = rows[0]
	for pos, r in enumerate(rows):
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
	for pos, block in enumerate(l):
		if block[0] == 0:
			lower_bound.append ( [(block[1][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
						0] )
		else:		
			cur_min=min([(r.end_point.gathered_on - r.start_point.gathered_on) if r != 0 else 0 for r in block ])	
			lower_bound.append ( [(block[0][start.gathered_on.epoch()]+3600 + block_seconds/2) * 1000,
				int(cur_min.total_seconds()) * 1000] )
	
	return {'data': lower_bound,'label':"Lower bound (%ss)" % block_seconds, 'id':'lower_bound_%s' %  block_seconds };

def __get_median_rows( rows, block_seconds=800, vertical_block_seconds=20, test=False):
	l = [] 
	first=True
	prev = rows[0]
	for pos, r in enumerate(rows):
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
	for pos, block in enumerate(l):
		if block[0] == 0:
			if test:
				mdate = block[1][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[1][start.gathered_on.epoch()]+3600
			median.append ( [ (seconds  + block_seconds/2) * 1000,	0] )
		else:
			initial_time_frame = min([(r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
			end_time_frame = max( [ (r[end.gathered_on.epoch()] - r[start.gathered_on.epoch()])  for r in block ] )
			n_windows = (end_time_frame - initial_time_frame) / vertical_block_seconds		
			windows = [0] * (n_windows + 1)
			values = ''
			#print windows
			#if len(block) <= 2:
			#	print 'WARNING', len(block)

			for ele in block:
				diff = (ele[end.gathered_on.epoch()] - ele[start.gathered_on.epoch()])
				cur_pos = (diff - initial_time_frame)  / vertical_block_seconds
				#print len(windows), cur_pos			
				windows[cur_pos] += 1
			#print windows
			tot = initial_time_frame + (vertical_block_seconds * windows.index(max(windows)))
			if test:
				mdate = block[0][start.gathered_on]
				seconds = (mdate-day).total_seconds()		
			else:
				seconds = block[0][start.gathered_on.epoch()]+3600
			#print seconds
			median.append ( [(seconds + block_seconds/2) * 1000,
					 (tot + (vertical_block_seconds/2))  * 1000] )
	if test:
		label = fdate.strftime('%a %d, %b' )
		#label += " [M(%(name)s)]" % {'name':block_seconds}
	else:
		label = "Median (%ss)" % block_seconds
	return {'data': median,'label':label, 'id':'median_%s' %  block_seconds };

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


#def download():
#    """
#    allows downloading of uploaded files
#    http://..../[app]/default/download/[filename]
#    """
#    return response.download(request, db)


#def call():
#    """
#    exposes services. for example:
#    http://..../[app]/default/call/jsonrpc
#    decorate with @services.jsonrpc the functions to expose
#    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
#    """
#    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())


#def saveDb():
#    return db.export_to_csv_file(open(request.folder+'/backup.csv', 'wb'))
#
#def restoreDb():
#    db.import_from_csv_file(open(request.folder+'backup.csv', 'rb'))
