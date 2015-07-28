from collections import OrderedDict
from gluon.dal import Expression
session.forget()

if request.function != 'wiki':
    from gluon.tools import Wiki
    response.menu += Wiki(auth).menu(controller="default", function="wiki")

# 21 bluetooth match type_id
# '2015-07-21' is a testing period
db_intime.elaborationhistory._common_filter = lambda query: ((db_intime.elaborationhistory.timestamp > '2015-07-15') &
                                                             (db_intime.elaborationhistory.type_id == 21))  
eh = db_intime.elaborationhistory
lb = db_intime.linkbasicdata
def index():
    # Dropdown
    stations = db_intime((eh.station_id == lb.station_id) & 
                         (lb.origin_id == db_intime.station.id)).select(db_intime.station.name, db_intime.station.id, 
                                                                    groupby=db_intime.station.id|db_intime.station.name,
                                                                    cacheable=True)

    return {'stations':stations}    

# Ajax call from D3.json    
def get_data():

    if ((request.vars.to) and (request.vars['from']) and
        request.vars.to.isdigit() and request.vars['from'].isdigit()):
        from_epoch = int(request.vars['from'][:-3])
        to_epoch = int(request.vars.to[:-3])
        db_intime.elaborationhistory._common_filter = lambda query: ((db_intime.elaborationhistory.timestamp.epoch() >= from_epoch) &
                                                                     (db_intime.elaborationhistory.timestamp.epoch() <= to_epoch) &
                                                                     (db_intime.elaborationhistory.type_id == 21))

    # Place the row with the selected station as first link, because only a direction link
    # can be visualized. A->B or B->A, including both cause a crash of D3
    # given that, the user can select which one between A or B should be placed before
    # Future works should allow users to select the order of all nodes, as C->D or D->C
    orderby=None
    if request.vars.station_id and request.vars.station_id.isdigit():
        station_id_start = int(request.vars.station_id)
        # Use sql case to place before the rows containing the selected station then, the other rows
        orderby = (lb.origin_id==station_id_start).case(1,2)

    cc = eh.station_id.count()
    query = (eh.station_id == lb.station_id)
    # Filter the datetime according to the day of the week
    days = None
    if request.vars.dow:
        days = map(lambda d: int(d),request.vars.dow) if isinstance(request.vars.dow, list) else [int(request.vars.dow)]
        dow = Expression(db, db._adapter.EXTRACT, eh.timestamp, 'dow', 'integer')
        query_day = (dow == days[0])
        for d in days[1:]:
            query_day |= (dow == d)
        query &= query_day
    # Selecting all possible match between all stations
    rows = db_intime(query).select(lb.origin_id, lb.destination_id, cc,
                                   groupby=lb.origin_id|lb.destination_id,
                                   orderby=orderby,
                                   cacheable=True)

    # Create a list of stations from the merge of stations as origin with stations as destination
    stations_orig = map(lambda r: r[lb.origin_id], rows)
    stations_dest = map(lambda r: r[lb.destination_id], rows)
    all_stations = list(set(stations_orig+stations_dest))   # set makes list unique

    # Query all necessary details, such as name, id etc
    nodes =  db_intime(db_intime.station.id.belongs(all_stations), 
                       ignore_common_filters=True).select(db_intime.station.name, db_intime.station.id, 
                                                          cacheable=True).as_list()

    # Create the output for D3
    links = []
    exclude_pairs = []
    pos_nodes = [node['id'] for node in nodes]
    for r in rows:
        orig_id, dest_id = r[lb.origin_id], r[lb.destination_id]
        pair = "%s_%s" % (orig_id, dest_id)
        pair_backward = "%s_%s" % (dest_id, orig_id)
        if pair_backward in exclude_pairs: 
            #print pair, 'excluded'
            continue
        exclude_pairs.append(pair)

        n_match = r[cc]
        if n_match != 0:
            pos_orig = pos_nodes.index(orig_id)
            pos_dest = pos_nodes.index(dest_id)
            links.append({'source': pos_orig, 'target': pos_dest, 'value': n_match})

    #import pprint
    #pprint.pprint( nodes)
    #pprint.pprint( links)
    return response.json({'links':links, 'nodes':nodes})
