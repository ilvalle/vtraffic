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
        t = self[table]
        for r in rows:
            self.__save_record(r, station_id, type_id, interval, t, unique)

        # Store the most recent record in the general table
        if table.endswith('history') and len(rows) != 0:
            t=self[table[:-len('history')]]
            self.__save_record(rows[-1], station_id, type_id, interval, t, unique=True, test_ts=False)

        self.commit()
        return len(rows)

    def __save_record(self, r, station_id, type_id, interval, t, unique, test_ts=True):
        from datetime import timedelta
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
            test = ((t.station_id == station_id) &
                    (t.type_id == type_id) &
                    (t.period == interval))
            if test_ts:
                test &= (t.timestamp == new_timestamp)
            t.update_or_insert(test,
                               **values)
        else:
            t.insert(**values)

    ### return the last timestamp for the given set or parameters (station, type, period)
    def get_last_ts(self, type_id, station_id, period, table):
        t = self[table]
        last_ts = self((t.type_id == type_id) &
                       (t.station_id == station_id) &
                       (t.period == period)).select(t.timestamp.max(), cacheable=True, limitby=(0,1), orderby_on_limitby=False).first()
        return last_ts[t.timestamp.max()]
