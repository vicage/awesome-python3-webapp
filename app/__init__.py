# -*- coding: utf-8 -*-

from flask import Flask
from flask import render_template
from flask import redirect, url_for, session, flash
from flask.ext.bootstrap import Bootstrap
from datetime import datetime
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from config import config            
from flask.ext.mail import Mail, Message
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_views = 'auth.login'
pagedown = PageDown()

def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	bootstrap.init_app(app)
	mail.init_app(app)
	moment.init_app(app)
	db.init_app(app)
	pagedown.init_app(app)
	login_manager.init_app(app)
	from .main import main as main_blueprint
	app.register_blueprint(main_blueprint)
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint, url_prefix = '/auth')
	#from .api import api as api_blueprint     #api还没有开发好
	#app.register_blueprint(api_blueprint, url_prefix = '/api')
	return app

