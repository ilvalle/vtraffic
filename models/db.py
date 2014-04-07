# -*- coding: utf-8 -*-


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
if not request.is_local:
	from gluon.contrib.memcache import MemcacheClient
	#from gluon.contrib.memdb import MEMDB
	memcache_servers = ['127.0.0.1:11211']
	cache.memcache = MemcacheClient(request, memcache_servers)
	cache.ram = cache.disk = cache.memcache
	#session.connect(request,response,db=MEMDB(cache.memcache))
	#session.connect(request,response,db)

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


db.define_table('station_type',
	Field('name'),
	auth.signature,
	format='%(name)s',
	migrate=False
)

db.define_table('station',
	Field('name'),
	Field("lat", "double", label=T('Latitude')),
	Field("lgt", "double", label=T('Longitude')),
	Field("station_type", 'reference station_type'),
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


#if "auth" in locals(): auth.wikimenu()
