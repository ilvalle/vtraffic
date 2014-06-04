import datetime
from datetime import timedelta

def box():
    session.forget()
    if not(request.vars.id) or not(request.vars.id.isdigit()): return 'specificare id (integer)'
    station_id = int(request.vars.id)
    time_delta = request.now - datetime.timedelta(days=1)
    query = (db.record.station_id == station_id) & (db.record.gathered_on > time_delta)
    empty = db(query).isempty()
    if empty:
        raise(HTTP(500, 'no logs'))
    else:
        return 'ok'        
