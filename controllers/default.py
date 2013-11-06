# -*- coding: utf-8 -*-
from __future__ import division
from applications.vtraffic.modules.tools import EPOCH_M
from datetime import timedelta
from gluon.utils import md5_hash
from itertools import groupby
import datetime, time
import operator

#start._common_filter = lambda query: start.gathered_on > period_limit
db.match._common_filter = lambda query: db.match.gathered_on_orig > period_limit

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
time_frame_size = int(request.vars.diff_temp) if request.vars.diff_temp and request.vars.diff_temp.isdigit() else 900


#@cache(request.env.path_info + '%s-%s-%s' % (id_origin, id_destination, time_frame_size) , time_expire=None, cache_model=cache.ram)
def compare_series():
	session.forget(response)

	day = db.match.gathered_on_orig.year() | db.match.gathered_on_orig.month() | db.match.gathered_on_orig.day()  
	# Gets the days with data 
	days = db( (db.match.station_id_orig == id_origin) ).select(
						db.match.gathered_on_orig.year(), 
						db.match.gathered_on_orig.month(), 
						db.match.gathered_on_orig.day(),
						groupby=day,
						orderby=day,
						cacheable = True)	

	out=[]
	# make the mode day by day
	for d in days:
		year  = d[db.match.gathered_on_orig.year()]
		month = d[db.match.gathered_on_orig.month()]
		day   = d[db.match.gathered_on_orig.day()]

		query = ((db.match.gathered_on_orig.year() == year) &
			 (db.match.gathered_on_orig.month() == month) &
			 (db.match.gathered_on_orig.day() == day) &
			 (db.match.gathered_on_dest.year() == year) &
			 (db.match.gathered_on_dest.month() == month) &
			 (db.match.gathered_on_dest.day() == day) &
			 (db.match.station_id_orig == id_origin) &
			 (db.match.station_id_dest == id_destination))


		#query_mode = (query_g & (start.station_id == id_origin) & (end.station_id == id_destination))
		#query_od = (query_g & (start.station_id == id_origin) & (end.station_id == id_destination))
		#query_do = (query_g & (start.station_id == id_destination) & (end.station_id == id_origin))
				
		data = __compute_mode(query, time_frame_size, 30, compare=True)
		#data = __compute_frequency(query_a, query_b, time_frame_size, compare=True)
		if len(data['data']) != 0:
			data['id'] = data['id'] + '%s%s%s' % (year,month,day)
			out.append(data)

	return response.render('generic.json', {'series':out})

#@cache(request.env.path_info + '%s-%s' % (id_origin, id_destination), time_expire=None, cache_model=cache.ram)
def get_series():
	session.forget(response)

#	rows = __get_rows_stations (id_origin,  id_destination)
#	query = (start.station_id == id_origin) & (end.station_id == id_destination) 
	query = (db.match.station_id_orig == id_origin) & (db.match.station_id_dest == id_destination) 
	logs=[]
#	for row in rows:
#		logs.append( [ row.start_point['epoch'] * 1000, row['elapsed_time'] * 1000 ]	)

	all_logs = []
	#all_logs.append( {'data':logs, 'label': 'matches', 'id':'logs'} )

	#for seconds in xrange(900, 1000, 100):
		#all_logs.append( __compute_lower(query, seconds ) )
	
	for seconds in xrange(900, 1000, 100):
		all_logs.append( __compute_mode(query, seconds) )
		#all_logs.append( __get_mode_rows(rows, seconds) )
	return response.render('generic.json', {'series':all_logs})
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


def __get_trend(station_id, block_seconds):
	query = start.station_id == station_id
	rows = db(query).select(start.gathered_on, 
							orderby=start.gathered_on,
							cache=(cache.ram, 3600),
			        		cacheable=True )
	blocks = __split2time_frame2(rows, block_seconds)

	out = [ [ ( EPOCH_M (block[0][db.record.gathered_on]) + block_seconds/2) * 1000, len(block) ] for block in blocks]
	return out

def __get_trend2(station_id, block_seconds):
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
	blocks_list = __get_blocks_scheduler (query, block_seconds, reset_cache=False)
	data = []	
	if (len(blocks_list) != 0):
		data = __wrapper_elaboration( blocks_list,
                                      __lower,
                                      block_seconds, 
                                      compare=compare)
	return {'data': data,'label':"Lower bound (%ss)" % block_seconds, 'id':'lower_bound_%s' %  block_seconds };

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

### Functions
# return the mode along a list of rows (block)
def __mode(block, block_seconds, vertical_block_seconds):
	block = sorted(block, key=operator.itemgetter('elapsed_time'))
	initial_time_frame = block[0].elapsed_time
	end_time_frame     = block[-1].elapsed_time
	mode_value = {'counter':0, 'seconds':0}
	i = 0
	for second in range(0,end_time_frame-initial_time_frame, MODE_STEP):
		current_initial = initial_time_frame + second
		current_end     = current_initial + vertical_block_seconds
		counter = 0
		while i < len(block):
			ele = block[i]
			if current_initial <= ele.elapsed_time < current_end:
				counter = counter + 1 
			elif current_end < ele.elapsed_time:
				break
			i = i + 1
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

def user():
    response.view = 'default/login.html'
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

# 
def __compute_frequency( query_a, query_r, block_seconds=800, compare=False):
	rows = __get_rows(query_a)
	if (len(rows) == 0):
		return  {'data': [],'label':'No matches', 'id':'mode_%s' %  block_seconds };

	block_list = __split2time_frame(rows, block_seconds)

	# get detected
	start_time = rows[0].start_point.gathered_on
	end_time   = rows[len(rows)-1].start_point.gathered_on
	station    = rows[0].start_point.station_id
	
	detected = db( 
			(db.record.station_id == station) & 
			(db.record.gathered_on > start_time) & 
			(db.record.gathered_on <= end_time) ).select(db.record.id, db.record.gathered_on, orderby=db.record.gathered_on)
	#print station, start_time, end_time, 'N: ', len(detected)
	reverse = __get_rows(query_r)
	
	remove = []	
	for d in detected:
		for r in reverse:
			if d.id == r.end_point.id:			#the start is the actual end in the reverse
				remove.append(d.id)

	detected_2 = [d for d in detected if d.id not in remove]
	print len(detected), len(remove), len(detected_2)
	detected_2 = sorted(detected_2, key=lambda d: d.gathered_on)

	if compare:
		first_date = block_list[0][0][start.gathered_on]
		day = datetime.datetime(first_date.date().year, first_date.date().month, first_date.date().day)
		reference_seconds = EPOCH_M(day)
		label = 'frequency_%s' % first_date.strftime('%a %d, %b' )
	else:
		reference_seconds = 0
		label = "Mode (%ss)" % block_seconds

	frequency=[]
	for block in block_list:
		if block[0] == 0:
			pass
			#seconds = block[1].start_point.epoch - reference_seconds
			#frequency.append ( [ (seconds + block_seconds/2) * 1000,	0] )
		elif len(block) <= 3:		# two values are not enough, lets pass
			pass
		else:
			seconds = block[0].start_point.epoch - (block[0].start_point.epoch % block_seconds) - reference_seconds
			start_block = block[0].start_point.gathered_on
			end_block = block[len(block)-1].start_point.gathered_on
			counter = 0
			for row in detected_2:
				if start_block <= row.gathered_on <= end_block:
					counter = counter + 1 
				elif end_block < row.gathered_on:
					break
			value = (len(block)/counter) * 100
			if value > 100:		
				print block, len(block), counter
			frequency.append ( [(seconds + block_seconds/2) * 1000, value] )

	return {'data': frequency,'label':label, 'id':'frequency_%s' %  block_seconds, 'yaxis': 2, 'bars':{'show':True, 'fill': 'true', 'align':'center', 'barWidth': block_seconds*1000}, 'lines': {'show':False, 'fill':False}, 'points': {'show':False} }



