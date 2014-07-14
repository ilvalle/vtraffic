import pytz
import datetime
import xmlrpclib
import httplib

EPOCH_REF = datetime.datetime(1970, 1, 1, 0, 0, tzinfo = pytz.utc)

def EPOCH_M(current_datetime):
	utc_datetime = pytz.utc.localize(current_datetime) # fix use rome and store data in utc instead of rome timezone
	delta = utc_datetime - EPOCH_REF
	seconds = delta.seconds + (delta.days * 24 * 3600)
	return seconds

__all__ = ['TimeoutTransport']

class TimeoutTransport(xmlrpclib.Transport):
    timeout = 20.0
    def set_timeout(self, timeout):
        self.timeout = timeout
    def make_connection(self, host):
        return httplib.HTTPConnection(host, timeout=self.timeout)

