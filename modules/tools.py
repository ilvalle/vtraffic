import pytz
import datetime
EPOCH_REF = datetime.datetime(1970, 1, 1, 0, 0, tzinfo = pytz.utc)

def EPOCH_M(current_datetime):
	utc_datetime = pytz.utc.localize(current_datetime) # fix use rome and store data in utc instead of rome timezone
	delta = utc_datetime - EPOCH_REF
	seconds = delta.seconds + (delta.days * 24 * 3600)
	return seconds
