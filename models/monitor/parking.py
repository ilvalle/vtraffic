db_intime.define_table('carparkingdynamichistory',
    Field('station_id', 'reference station'),
    Field('carparkstate', 'string'),
    Field('carparktrend', 'string'),
    Field('exitrate', 'double'),
    Field('fillrate', 'double'),
    Field('lastupdate', 'datetime'),
    Field('occupacy', 'integer'),    
    Field('occupacypercentage', 'double'),    
    migrate=False
)
