# -*- coding: utf-8 -*-
from applications.vtraffic.modules.tools import intimeDAL

MIGRATE=False
# user and pwd are defined in a different and not public model.
db = DAL('postgres://%s:%s@10.8.0.1:5432/integreen' % (user, pwd),
	migrate=MIGRATE,
	migrate_enabled=MIGRATE,
	#fake_migrate_all=True,
	lazy_tables=not(MIGRATE),
	pool_size=3
)

cache.memcache = cache.ram
#if not request.is_local:
#	from gluon.contrib.memcache import MemcacheClient
#	#from gluon.contrib.memdb import MEMDB
#	memcache_servers = ['127.0.0.1:11211']
#	cache.memcache = MemcacheClient(request, memcache_servers)
#	cache.ram = cache.disk = cache.memcache
#	#session.connect(request,response,db=MEMDB(cache.memcache))
#	#session.connect(request,response,db)

## (optional) optimize handling of static files
#response.optimize_css = 'concat,minify'
#response.optimize_js = 'concat,minify'
#session.forget(response)
from gluon.tools import Auth
auth = Auth(db)

## create all tables needed by auth if not custom tables
auth.define_tables(username=True, migrate=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'smtp.digital.tis.bz.it:25'
mail.settings.sender = 'project@integreen-life.bz.it'
#mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = True
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')
auth.settings.allow_basic_login = True
auth.settings.wiki.controller = 'default'
auth.settings.wiki.function   = 'wiki'
db.auth_user.email.widget = lambda f,v: SQLFORM.widgets.string.widget(f, v,_placeholder=T('Email'), _class="input-block-level")
db.auth_user.username.widget = lambda f,v: SQLFORM.widgets.string.widget(f, v,_placeholder=T('Username'), _class="input-block-level")
db.auth_user.password.widget = lambda f,v: SQLFORM.widgets.string.widget(f, v, _placeholder=T('Password'), _class="input-block-level", _type="password")
T.is_writable = False


#db.define_table('station_type',
#	Field('name'),
#	auth.signature,
#	format='%(name)s',
#	migrate=False
#)

db.define_table('station',
	Field('name'),
	Field("lat", "double", label=T('Latitude')),
	Field("lgt", "double", label=T('Longitude')),
	Field("last_check_on", "datetime"),
#	Field("station_type", 'reference station_type'),
	Field("dtype"),
#	Field('log_file', 'upload'),
	auth.signature,
	format='%(name)s',
	migrate=False
)

#db.define_table('log',
#	Field('station_id', 'reference station'),
#	Field('log_file', 'upload'),
#	auth.signature
#	, migrate=False
#)

db.define_table('record',
	Field('station_id', 'reference station'),
#	Field('log_id', 'reference log'),
	Field('mac', 'string', length=18),
	Field('gathered_on', 'datetime'),
	Field('utc_in_ms', 'integer'),
	Field('version', 'integer'),
	Field('valid', 'boolean'),
	migrate=False
)

db.define_table('match',
	Field('station_id_orig', 'reference station'),
	Field('station_id_dest', 'reference station'),
	Field('epoch_orig', 'integer' ),
	Field('epoch_dest', 'integer' ),
	Field('gathered_on_orig', 'datetime' ),
	Field('gathered_on_dest', 'datetime' ),
	Field('elapsed_time', 'integer' ),
	Field('record_id_orig', 'reference record' ),
	Field('record_id_dest', 'reference record' ),
	Field('overtaken', 'boolean'),
	migrate=False
)


from gluon.dal import ADAPTERS, PostgreSQLAdapter

class ExtendedPostgreSQLAdapter(PostgreSQLAdapter):
    def ST_NPOINTS(self, first):
        """
        http://postgis.org/docs/ST_NPoints.html
        """
        return 'ST_NPoints(%s)' % (self.expand(first))

    def ST_DUMPPOINTS(self, first):
        """
        http://postgis.org/docs/ST_DumpPoints.html
        """
        return '(ST_DumpPoints(%s)).geom' % (self.expand(first))
        
    

ADAPTERS.update( {
    'intimepostgres': ExtendedPostgreSQLAdapter
})


MIGRATE=False
db_intime = intimeDAL('intimepostgres://%s:%s@10.8.0.1:5432/integreenintime' % (user, pwd),
	migrate=MIGRATE,
	migrate_enabled=MIGRATE,
	#fake_migrate_all=True,
	lazy_tables=not(MIGRATE),
	pool_size=3
)

db_intime.executesql("set search_path to 'intime', 'public';")

db_intime.define_table('station',
    Field('name', 'string'),
    Field('shortname'),
    Field('description'),
    Field('stationtype'),
    #Field('pointprojection'),
    Field('stationcode'),
    Field('active'),
    #Field('parent_id', 'reference station'),
    migrate=False,
    format="%(name)s",
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ],
)

db_intime.define_table("linkbasicdata",
    Field('station_id', "reference station", label='Station'),
    Field('origin_id', "reference station", label="Origin station"),
    Field('destination_id', "reference station", label="Destination station"),
    Field('street_ids_ref', 'list:reference streetbasicdata'),
    Field('length', 'double'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ],
    format="%(station_id)s",
)



db_intime.define_table('type',
    Field('cname'),
    Field('created_on', 'datetime'),
    Field('cunit'),
    Field('description'),
    Field('rtype'),
    format="%(cname)s",
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)

db_intime.define_table('elaboration',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'double'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('elaborationhistory',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'double'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),    
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)

db_intime.define_table('measurement',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'double'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),    
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('measurementhistory',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'double'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('measurementstring',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'string'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),    
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('measurementstringhistory',
    Field('created_on', 'datetime'),
    Field('timestamp', 'datetime'),
    Field('value', 'string'),
    Field('station_id', 'reference station'),
    Field('type_id', 'reference type'),
    Field('period', 'integer'),    
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('trafficstreetfactor',
    Field('id_arco', 'reference station'),
    Field('id_spira', 'reference station'),
    Field('factor', 'double'),
    Field('length', 'double'),
    Field('hv_perc', 'double'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('streetbasicdata',
    Field('station_id', 'reference station'),
    Field('length', 'double'),
    Field('description', 'string'),
    Field('speed_default', 'double'),
    Field('linegeometry', 'geometry()'),    
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('copert_parcom',
    Field('percent', 'double'),
    Field('descriz', 'string'),
    Field('id_class', 'integer'),
    Field('eurocl', 'integer'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('copert_emisfact',
    Field('type_id', 'reference type'),
    Field('copert_parcom_id', 'reference copert_parcom'),
    Field('v_min', 'integer'),
    Field('v_max', 'integer'),
    Field('coef_a', 'double'),
    Field('coef_b', 'double'),
    Field('coef_c', 'double'),
    Field('coef_d', 'double'),
    Field('coef_e', 'double'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)
db_intime.define_table('measurementmobilehistory',
    Field('no2_1_ppb', 'double'),
    Field('ts_ms', 'datetime'),
    Field('no2_1_microgm3_ma', 'double'),
    Field('gps_1_speed_mps', 'double'),
    Field('no2_1_microgm3_exp', 'double'),
    Field('station_id', 'reference station'),
    Field('id_vehicle_nr', 'integer'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)

db_intime.define_table('classification',
    Field('type_id', 'reference type'),
    Field('threshold', 'string', requires=IS_IN_SET(['black', 'red', 'yellow', 'green'])),
    Field('min', 'double'),
    Field('max', 'double'),
    migrate=False,
    on_define=lambda table: [
        table.id.set_attributes(readable = False),
        #table.__setitem__('create', auth.has_membership('siteadmin')),
    ]
)

if not request.controller:
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Linkstation'
cmd_options = request.global_settings.cmd_options
if cmd_options and cmd_options.scheduler or request.controller in ['plugin_cs_monitor', 'test', 'monitor']:
    response.models_to_run.append("^scheduler/\\w+\\.py$")

#if "auth" in locals(): auth.wikimenu()
