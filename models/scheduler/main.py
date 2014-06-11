from itertools import groupby
from gluon.scheduler import Scheduler
scheduler = Scheduler(db, migrate=False)

from applications.vtraffic.modules.tools import EPOCH_M
from datetime import timedelta
import datetime
import time

def test_write():
    db.define_table('test_write',
        Field('value', 'integer' ),
        migrate=True
    )
    insert_id = db.test_write.insert(value=123)
    n_insert  = db(db.test_write).count()
    db.commit()
    return (insert_id, n_insert)

## For each possible origin/destination couple finds the matches
def run_all():
    db.station._common_filter = lambda query: db.station.is_active == True
    stations = db(db.station.id).select(db.station.id, orderby=db.station.id, cacheable = True)
    total = 0
    for o in stations:
        for d in stations:
            if o.id != d.id:
                matches = find_matches(o.id, d.id)
                __save_match(matches)
                total += len(matches)

    return total

## Set all record to valid=False if there are null mac address
def run_valid_record():
    rows = db((db.record.mac == '00:00:00:00:00:00') & (db.record.valid == None)).select(db.record.ALL)
    for r in rows:
        r.update_record(valid=False)
    db.commit()
    return len(rows)

# compute and store the mode in the intime database    
def run_mode():
    type_id = 18
    interval = 900
    link_stations = db_intime(db_intime.linkbasicdata.station_id == db_intime.station.id).select()
    for link in link_stations:
        origin = link.linkbasicdata.origin
        destination = link.linkbasicdata.destination
        db.match._common_filter = None
      	query = (db.match.station_id_orig == origin) & (db.match.station_id_dest == destination) 
        # Given an origin and a destination, we check the last stored match
        last_value = db_intime(db_intime.elaborationhistory.station_id == link.linkbasicdata.station_id).select(limitby=(0,1), orderby=~db_intime.elaborationhistory.timestamp)
        # manca order by
        if last_value:
            query &= (db.match.gathered_on_orig > (last_value[0].timestamp + timedelta(seconds=last_value[0].period/2)))
        #print query
        data = __compute_mode(query, 900)['data']
        # save all data into elaborationhistory
        # TODO fix timezone
        rows = [{'timestamp': datetime.datetime.fromtimestamp(r[0]/1000 - 7200), 'value': r[1]/1000 if r[1] else 0} for r in data]
        # Save the data
        __save_elaboration(rows, link.linkbasicdata.station_id, type_id, interval)
        out = '%s %s - stored -> %s' % (origin, destination, len(data))
        
    #link_stations = db_intime(db_intime.elaboration).select()    
    #elaboration
    # created_on    -> datetime.now
    # timestamp     -> output elaboration
    # value         -> output elaboration
    # station_id    -> link.linkbasicdata.station_id
    # type_id       -> 18
    # period        -> 900
    ## Type operation is 18 for frame 15minutes long
    return out
    



def find_matches (id_origin, id_destination, query=None):
    t0 = time.time()
    # find last stored match for the given couple of origin/destination
    last_match_query = db( (db.match.station_id_orig == id_origin) & 
                     (db.match.station_id_dest == id_destination) &
                     (db.match.record_id_dest == db.record.id) )._select(db.record.gathered_on,
                     orderby = ~db.match.epoch_dest, cacheable = True, limitby=(0,1) )
    last_match = db.executesql(last_match_query, as_dict=True)

    t1 = time.time()
    query_od = (start.station_id == id_origin) & (end.station_id == id_destination) if not query  else query
    if last_match:
        initial_data = last_match[0]['gathered_on'] - __next_step()
    #print id_origin, id_destination, last_match
    matches = []
    n_prev_matches = 1
    while len(matches) != n_prev_matches:
        n_prev_matches = len(matches)
        if last_match:
            # The constraint (end.gathered_on > initial_data) reduces the number of rows to sort before the left join
            query = query_od & (start.gathered_on > initial_data ) & (end.gathered_on > initial_data)
            initial_data = initial_data - __next_step()
            #print len(db(query).count())
            #if (db(query).isempty()):
            #    print 'is_empty'
            #    matches = []
            #    continue
            matches = __get_rows(query, use_cache=False)
            #print 'm', len(matches)
            matches = __clean_progress_matches(matches, last_match[0]['gathered_on']) 
        else:
            matches = __get_rows(query_od, use_cache=False)
            n_prev_matches = len(matches)         # force to stop
    t2 = time.time()
    #print "%s vs %s" % (id_origin, id_destination), t1-t0, t2-t1
    return matches

        
### Utility functions
# store computed matches in the db
def __save_match(matches):
    for r in matches:
        db.match.insert( station_id_orig=r.start_point.station_id,
                         station_id_dest=r.end_point.station_id,
                         epoch_orig=r.start_point.epoch,
                         epoch_dest=r.end_point.epoch,
                         gathered_on_orig=r.start_point.gathered_on,
                         gathered_on_dest=r.end_point.gathered_on,
                         elapsed_time=r.elapsed_time,
                         record_id_orig=r.start_point.id,
                         record_id_dest=r.end_point.id,
                         overtaken=False )
    if len(matches) != 0:    
        db.commit()
    return len(matches)

# this constraint must be executed after remove_dup 
def __clean_progress_matches(matches, destination_min_date):
    output = [ m for m in matches if m.end_point.gathered_on > destination_min_date ]
    return output    

# Return a timedelta value based on the current one
def __next_step(current=None):
    if current:    # incremental approach
        minutes = 15     
    else:    # initial step value
        minutes = 15        # it'll be the avg/min/mode elapsed_time
    
    return timedelta(minutes=minutes)
    
def count_bluetooth():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Bluetoothstation'
    stations = db_intime(db_intime.station.id).select(cacheable=True)
    total = 0
    for s in stations:
        total += count_bluetooth_station(station_id = s.id, interval = 900)
    return total 
    
### For each bluetooth statioin, count the number of bluetooth gathered in a window of 15minutes
def count_bluetooth_station(station_id, interval): 
    type_id = 19     # Elaboration type is 19
    ### check last value or set it as min(gathered_on)

    last_ts = db_intime((db_intime.elaborationhistory.type_id == type_id) & 
                        (db_intime.elaborationhistory.station_id == station_id)).select(db_intime.elaborationhistory.timestamp.max()).first()
    if last_ts[db_intime.elaborationhistory.timestamp.max()]:
        last_ts = "'%s'" % (last_ts[db_intime.elaborationhistory.timestamp.max()] - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(gathered_on)::date'
    query = """
        SELECT start_time as timestamp, count(e.id) AS n_bluetooth
        FROM (
           SELECT start_time, lead(start_time, 1, now()::timestamp) OVER (ORDER BY start_time) AS end_time
           FROM ( SELECT generate_series(%(since)s, max(gathered_on), '%(interval)s seconds'::interval) AS start_time from record where station_id = %(station_id)s) x
           ) as g
        left JOIN (select gathered_on, id from record where station_id = %(station_id)s) e ON e.gathered_on >= g.start_time AND e.gathered_on < g.end_time
        GROUP  BY start_time
        ORDER  BY start_time asc;
    """ % {'station_id': station_id, 'since': last_ts, 'interval':interval}
    rows = db.executesql(query, as_dict=True) 

    rows = [{'timestamp': r['timestamp'], 'value':r['n_bluetooth'] } for r in rows]
    # Save the data
    __save_elaboration(rows, station_id, type_id, interval)
    
    return len(rows)

## save everything in elaborationhistory & elaboration
def __save_elaboration(rows, station_id, type_id, interval):
    for r in rows:
        new_timestamp = r['timestamp'] + datetime.timedelta(seconds=interval/2)
        db_intime.elaborationhistory.update_or_insert( (db_intime.elaborationhistory.timestamp == new_timestamp) & 
                                                       (db_intime.elaborationhistory.station_id == station_id) &
                                                       (db_intime.elaborationhistory.type_id == type_id) &
                                                       (db_intime.elaborationhistory.period == interval), 
                    created_on= datetime.datetime.now(),
                    timestamp = new_timestamp,
                    value = r['value'],
                    station_id = station_id,
                    type_id = type_id,
                    period  = interval)
                    
    db_intime.commit()
    return

def count_match():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Linkstation'
    stations = db_intime(db_intime.station.id).select(cacheable=True)
    total = 0
    for s in stations:
        total += count_matches_station(station_id = s.id, interval=900)
    return total 
    
### For each bluetooth statioin, count the number of bluetooth gathered in a window of 15minutes
def count_matches_station(station_id, interval): 
    type_id = 20     # Elaboration type is 19

    ### check last value or set it as min(gathered_on)
    row = db_intime((db_intime.station.id == station_id) & (db_intime.linkbasicdata.station_id == db_intime.station.id)).select(db_intime.linkbasicdata.ALL, cacheable=True).first()
    station_id_orig = row.origin
    station_id_dest = row.destination
    
    last_ts = db_intime((db_intime.elaborationhistory.type_id == type_id) & 
                        (db_intime.elaborationhistory.station_id == station_id)).select(db_intime.elaborationhistory.timestamp.max()).first()
    
    if last_ts[db_intime.elaborationhistory.timestamp.max()]:
        last_ts = "'%s'" % (last_ts[db_intime.elaborationhistory.timestamp.max()] - datetime.timedelta(seconds=interval/2))
    else:
        last_ts = 'min(gathered_on_orig)::date'

    query = """
        SELECT start_time as timestamp, count(e.id) AS n_match
        FROM (
           SELECT start_time, lead(start_time, 1, now()::timestamp) OVER (ORDER BY start_time) AS end_time
           FROM ( SELECT generate_series(%(since)s, max(gathered_on_orig), '%(interval)s seconds'::interval) AS start_time 
                  FROM   match 
                  WHERE  station_id_orig = %(station_id_orig)s AND station_id_dest = %(station_id_dest)s) x
           ) as g
        left JOIN (SELECT gathered_on_orig, id FROM match where station_id_orig = %(station_id_orig)s AND station_id_dest = %(station_id_dest)s) e ON e.gathered_on_orig >= g.start_time AND e.gathered_on_orig < g.end_time
        GROUP  BY start_time
        ORDER  BY start_time asc;
    """ % {'station_id_orig': station_id_orig,'station_id_dest': station_id_dest, 'since': last_ts, 'interval':interval}
    rows = db.executesql(query, as_dict=True) 

    rows = [{'timestamp': r['timestamp'], 'value':r['n_match'] } for r in rows]
    # Save the data
    __save_elaboration(rows, station_id, type_id, interval)
                  
    return len(rows)
        

