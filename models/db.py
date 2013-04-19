# -*- coding: utf-8 -*-


MIGRATE=False
## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()
db = DAL('postgres://web2py:web2py@localhost:5432/traffic', 
	migrate=MIGRATE,
	migrate_enabled=MIGRATE,
	lazy_tables=not(MIGRATE),
	pool_size=3
)

cache.memcache = cache.ram
if not request.is_local:
	from gluon.contrib.memcache import MemcacheClient
	#from gluon.contrib.memdb import MEMDB
	memcache_servers = ['127.0.0.1:11211']
	cache.memcache = MemcacheClient(request, memcache_servers)
	cache.ram = cache.disk = cache.memcache
	#session.connect(request,response,db=MEMDB(cache.memcache))
	#session.connect(request,response,db)

## (optional) optimize handling of static files
response.optimize_css = 'concat,minify'
response.optimize_js = 'concat,minify'
from gluon.tools import Auth
auth = Auth(db)
## create all tables needed by auth if not custom tables
auth.define_tables(username=True, migrate=MIGRATE)

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
T.is_writable = False

db.define_table('station',
	Field('name'),
	Field("lat", "double", label=T('Latitude')),
        Field("lgt", "double", label=T('Longitude')),
        Field("alt", "double", label=T('altitude')),
	Field('log_file', 'upload'),
	auth.signature,
	format='%(name)s'
)

db.define_table('log',
	Field('station_id', 'reference station'),
	Field('log_file', 'upload'),
	auth.signature
)

db.define_table('record',
	Field('station_id', 'reference station'),
	Field('log_id', 'reference log'),
	Field('mac', 'string', length=18),
	Field('gathered_on', 'datetime'),
)	
	

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
