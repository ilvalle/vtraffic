import datetime
from datetime import timedelta

session.forget()
def box():
    if not(request.vars.id) or not(request.vars.id.isdigit()): return 'specificare id (integer)'
    station_id = int(request.vars.id)
    db_intime.station._common_filter = lambda query: ((db_intime.station.stationtype == 'Bluetoothstation') &
                                                      (db_intime.station.id == station_id))
    return __check_history('Bluetooth', 'measurementstringhistory')

def scheduler():
    query = (db.scheduler_task.status == 'FAILED')
    empty = db(query).isempty()
    if not(empty):
        raise(HTTP(500, 'task failed'))
    else:
        return 'ok'
        
def situation():
    if not(auth.is_logged_in()):
        db.station.id.readable=False
    db_intime.station._common_filter = lambda query: (db_intime.station.stationtype == 'Bluetoothstation')
    grid = SQLFORM.grid(db_intime.station, csv=False, searchable=False)
    return {'grid':grid}

def meteo():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Meteostation'
    return __check_measurementhistory('Meteo')

def environment():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Environmentstation'
    return __check_measurementhistory('Environment')
    
def parking():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'ParkingStation'
    return __check_parkinghistory()

def parking_forecast():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'ParkingStation'
    return __check_measurementhistory('parking-forecast')

# check for each type if the data is not older than 1day
def __check_measurementhistory(name):
    return __check_history(name, 'measurementhistory')

def __check_history(name, table):
    time_delta = request.now - datetime.timedelta(days=1)
    t = db_intime[table]
    max_ts = t.timestamp.max()
    query = (t.station_id == db_intime.station.id) & \
            (t.type_id == db_intime.type.id) & \
            (t.timestamp > time_delta)
    query_having = (max_ts > time_delta)
    id_list = db_intime(query).select(t.type_id, t.station_id, cacheable=True, limitby=(0,1),
                                      groupby=t.station_id | t.type_id, having=query_having).as_list()
    if len(id_list) == 0:
        raise(HTTP(500, '%s logs are older than 1day, %s' % (name, id_list)))
    else:
        return 'ok'

# check for each type if the data is not older than 1day
def __check_parkinghistory():
    time_delta = request.now - datetime.timedelta(days=1)
    max_ts = db_intime.carparkingdynamichistory.lastupdate.max()
    query = (db_intime.carparkingdynamichistory.station_id == db_intime.station.id)
    query_having = (max_ts < time_delta)
    id_list = db_intime(query).select(db_intime.carparkingdynamichistory.station_id, cacheable=True, 
                                      groupby=db_intime.carparkingdynamichistory.station_id, having=query_having).as_list()
    if len(id_list) != 0:
        raise(HTTP(500, '%s logs are older than 1day, %s' % ('Parking', id_list)))
    else:
        return 'ok'

def parking_3rd_parties():
    try:
        from xmlrpclib import ServerProxy
        from applications.vtraffic.modules.tools import TimeoutTransport
        provider = ServerProxy("http://84.18.134.218:7075/RPC2", transport=TimeoutTransport())
        parking_list = provider.pGuide.getElencoIdentificativiParcheggi()
        assert len(parking_list) != 0
        for p in parking_list:
            value = provider.pGuide.getPostiLiberiParcheggioExt(p)
            print value
            assert value != None
        return 'ok'
    except:
        raise(HTTP(500, 'Provider is either unreachable or no data were transferred'))
