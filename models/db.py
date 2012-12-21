# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()
#migrate=False,
db = DAL('sqlite://storage.sqlite', 
	migrate=False,	
	lazy_tables=True)
##session.connect(request, response, db=db)
## or store session in Memcache, Redis, etc.
## from gluon.contrib.memdb import MEMDB
## from google.appengine.api.memcache import Client
## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
#response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, prettydate
auth = Auth(db)
from gluon.tools import Crud, Service, PluginManager
crud, service, plugins = Crud(db), Service(), PluginManager()

#try:
#	pd = local_import('private_data')
#except:
#	print 'provide a personal data file'

## create all tables needed by auth if not custom tables
auth.define_tables(username=True)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = True
auth.settings.reset_password_requires_verification = True
#auth.settings.actions_disabled.append('register')

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
#from gluon.contrib.login_methods.rpx_account import use_janrain
#use_janrain(auth, filename='private/janrain.key')

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
	Field('mac'),
	Field('gathered_on', 'datetime'),
)	
	

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
