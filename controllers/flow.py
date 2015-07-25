from collections import OrderedDict

# 21 bluetooth match type_id
# '2015-07-21' is a testing period
db_intime.elaborationhistory._common_filter = lambda query: ((db_intime.elaborationhistory.timestamp > '2015-07-21') & 
                                                             (db_intime.elaborationhistory.type_id == 21))  
eh = db_intime.elaborationhistory
lb = db_intime.linkbasicdata
def index():
    # Dropdown
    stations = db_intime((eh.station_id == lb.station_id) & 
                         (lb.origin_id == db_intime.station.id)).select(db_intime.station.name, db_intime.station.id, 
                                                                    groupby=db_intime.station.id|db_intime.station.name,
                                                                    cacheable=True, cache=(cache.ram, 60))

    return {'stations':stations}    

# Ajax call from D3.json    
def get_data():
    cc = eh.station_id.count()
    # Selecting all possible match between all stations
    rows = db_intime(eh.station_id == lb.station_id).select(lb.origin_id, lb.destination_id, cc, 
                                                            groupby=lb.origin_id|lb.destination_id, 
                                                            cacheable=True, cache=(cache.ram, 60)).as_list()
    # Create a list of stations from the merge of stations as origin with stations as destination
    stations_orig = map(lambda r: r['linkbasicdata']['origin_id'], rows)
    stations_dest = map(lambda r: r['linkbasicdata']['destination_id'], rows)    
    all_stations = list(set(stations_orig+stations_dest))   # set makes list unique

    # Query all necessary details, such as name, id etc
    nodes =  db_intime(db_intime.station.id.belongs(all_stations), 
                       ignore_common_filters=True).select(db_intime.station.name, db_intime.station.id, 
                                                          cacheable=True, cache=(cache.ram, 60)).as_list()

    # Create the output for D3
    # Place the row with the selected station as first link, because only a direction link 
    # can be visualized. A->B or B->A, including both cause a crash of D3
    # given that, the user can select which one between A or B should be placed before
    # Future works should allow users to select the order of all nodes, as C->D or D->C
    if request.vars.station_id and request.vars.station_id.isdigit():
        station_id_start = int(request.vars.station_id)
        ele = next((item for item in rows if item['linkbasicdata']['origin_id'] == station_id_start), None)
        rows.insert(0, rows.pop(rows.index(ele)))

    links = []
    exclude_pairs = []
    pos_nodes = [node['id'] for node in nodes]
    for r in rows:
        orig_id, dest_id = r['linkbasicdata']['origin_id'], r['linkbasicdata']['destination_id']
        pair = "%s_%s" % (orig_id, dest_id)
        pair_backward = "%s_%s" % (dest_id, orig_id)
        if pair_backward in exclude_pairs: 
            #print pair, 'excluded'
            continue
        exclude_pairs.append(pair)

        n_match = r['_extra']['%s' % cc]
        if n_match != 0:
            pos_orig = pos_nodes.index(orig_id)
            pos_dest = pos_nodes.index(dest_id)
            links.append({'source': pos_orig, 'target': pos_dest, 'value': n_match})

    #import pprint
    #pprint.pprint( nodes)
    #pprint.pprint( links)
    return response.json({'links':links, 'nodes':nodes})
