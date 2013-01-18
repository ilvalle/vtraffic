# -*- coding: utf-8 -*-


MIGRATE=False
## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()
db = DAL('postgres://web2py:web2py@localhost:5432/traffic', 
	migrate=MIGRATE,
	migrate_enabled=MIGRATE,
	lazy_tables=False,
)

if not request.is_local:
	from gluon.contrib.memcache import MemcacheClient
	#from gluon.contrib.memdb import MEMDB
	memcache_servers = ['127.0.0.1:11211']
	cache.memcache = MemcacheClient(request, memcache_servers)
	cache.ram = cache.disk = cache.memcache
	#session.connect(request,response,db=MEMDB(cache.memcache))

## (optional) optimize handling of static files
#response.optimize_css = 'concat,minify,inline'
response.optimize_js = 'concat,minify,inline'
from gluon.tools import Auth
auth = Auth(db)
## create all tables needed by auth if not custom tables
auth.define_tables(username=True, migrate=MIGRATE)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = True
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled.append('register')
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
