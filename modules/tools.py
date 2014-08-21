import pytz
import datetime
import xmlrpclib
import httplib
from gluon.dal import DAL

EPOCH_REF = datetime.datetime(1970, 1, 1, 0, 0, tzinfo = pytz.utc)

def EPOCH_M(current_datetime):
	utc_datetime = pytz.utc.localize(current_datetime) # fix use rome and store data in utc instead of rome timezone
	delta = utc_datetime - EPOCH_REF
	seconds = delta.seconds + (delta.days * 24 * 3600)
	return seconds

__all__ = ['TimeoutTransport', 'intimeDAL']

class TimeoutTransport(xmlrpclib.Transport):
    timeout = 20.0
    def set_timeout(self, timeout):
        self.timeout = timeout
    def make_connection(self, host):
        return httplib.HTTPConnection(host, timeout=self.timeout)


class intimeDAL(DAL):
    ## save everything in elaborationhistory
    def save_elaborations(self, rows, station_id, type_id, interval, unique=True):
        return self.__save_records(rows, station_id, type_id, interval, table='elaborationhistory', unique=unique)

    ## save everything in measurementhistory
    def save_measurements(self, rows, station_id, type_id, interval, unique=True):
        return self.__save_records(rows, station_id, type_id, interval, table='measurementhistory', unique=unique)

    ## save data in a general intime table
    def __save_records(self, rows, station_id, type_id, interval, table, unique=True):
        from datetime import timedelta
        t = self[table]

        for r in rows:
            if interval != 1:
                new_timestamp = r['timestamp'] + timedelta(seconds=interval/2)
            else:
                new_timestamp = r['timestamp']
            values = {'created_on':datetime.datetime.now(),
                      'timestamp': new_timestamp,
                      'value': r['value'],
                      'station_id': station_id,
                      'type_id': type_id,
                      'period': interval}
            if unique:
                t.update_or_insert(((t.timestamp == new_timestamp) &
                                    (t.station_id == station_id) &
                                    (t.type_id == type_id) &
                                    (t.period == interval)),
                                   **values)
            else:
                t.insert(**values)

        self.commit()
        return len(rows)
