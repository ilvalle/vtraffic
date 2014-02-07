import requests

# TODO 
# click on the well title collapse the well
# check if a well i alresdy there, if not load it, otherwise fire a message
# keep the same zoom and pan while reloading data
# 
#response.headers['web2py-component-flash'] = ''
seconds = int(datetime.timedelta(seconds=3600).total_seconds())

# temp fix due to double menu
zero = request.args(0) or 'index'
if request.function != 'wiki' and zero and not(zero.isdigit()):
	from gluon.tools import Wiki
	response.menu += Wiki(auth, migrate=False).menu(function="wiki")
baseurl = "http://ipchannels-test.integreen-life.bz.it"
# ipchannels-test.integreen-life.bz.it/MeteoFrontEnd/get-records?station=8320&name=WG&unit=m/s&seconds=3000
 
def index():
	frontends = ['MeteoFrontEnd', 'VehicleFrontEnd']
	return response.render('console/index.html', {'frontends':frontends, 'seconds':seconds})

def get_stations():
    frontend = request.vars.frontend
    if not frontend:
        response.headers['web2py-component-flash'] = 'Select something'
        response.headers['web2py-component-content'] = 'hide'
        return ''
    response.headers['web2py-component-content'] = 'append'
    url = "%s/%s/rest/get-stations" % (baseurl, frontend)
    r = requests.get(url) # params=url_vars)
    stations = r.json()
    response.headers['web2py-component-content'] = 'hide'
    response.headers['web2py-component-command'] = "add_after_form(xhr, 'form_frontend');"
    return response.render('console/stations_form.html', {'stations':stations, 'frontend':frontend})


def get_data_types():
    station = request.vars.station
    frontend = request.vars.frontend
    if not (frontend and station):
        response.headers['web2py-component-flash'] = 'Select something'
        response.headers['web2py-component-content'] = 'hide'
        return ''
    response.headers['web2py-component-content'] = 'hide'
    response.headers['web2py-component-command'] = "append_to_sidebar(xhr, 'sidebar_console');"
    url = "%s/%s/rest/get-data-types" % (baseurl, frontend)
    r = requests.get(url, params={'station':station})
    data_types = r.json()

    return response.render('console/data_types_legend.html', {'data_types':data_types, 'frontend':frontend, 'station':station })


def get_data():
    frontend = request.vars.frontend
    station = request.vars.station 
    data_type = request.vars.data_type
    data_label = request.vars.data_label
    unit = request.vars.unit
    seconds = request.vars.seconds
#    print 'f', frontend
#    print 's', station
#    print 'd', data_type
#    print 'u', unit
#    print 's', seconds
#    print 'l', data_label
    
    url = "%s/%s/rest/get-records" % (baseurl, frontend)
    params = {'station':station, 'name':data_type, 'unit':unit, 'seconds':seconds}
    r = requests.get(url, params=params)
    data = r.json()
    output = [ [row['timestamp'] if 'timestamp' in row else row['ts_ms'], row['value']] for row in data ]
    # the id must be the same of the A element in the data type list
    series = [{'data':output, 'id': 'type_%s_%s' % (station,data_type), 'station_id':'station_iud', 'label': "%s - %s" % (station, data_label)}]
    return response.json({'series': series})

