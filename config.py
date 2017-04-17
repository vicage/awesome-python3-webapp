# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	SECRET_KEY = 'hard to guess string'
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	FLASK_MAIL_SUBJECT_PREFIX = '[Flasky]'
	FLASK_MAIL_SENDER = 'Flasky Admin <kaijie.yang@karakal.com.cn>'
	FLASKY_ADMIN = '792187427@qq.com'
	ALICY_POSTS_PER_PAGE = 20
	ALICY_COMMENTS_PER_PAGE = 60
	
	@staticmethod
	def init_app(app):
		pass
		
class DevelopmentConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.exmail.qq.com'
	MAIL_USERNAME = 'kaijie.yang@karakal.com.cn'
	MAIL_PASSWORD = '1234567Ykj'
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://review:Jstdit@112@192.168.11.129:3306/crashcourse'
	
class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://review:Jstdit@112@192.168.11.129:3306/crashcourse'
	
class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://review:Jstdit@112@192.168.11.129:3306/crashcourse'
	
config = {
	'development' : DevelopmentConfig,
	'testing' : TestingConfig,
	'production' : ProductionConfig,
	'default' : DevelopmentConfig
}