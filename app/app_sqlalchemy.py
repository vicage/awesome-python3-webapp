# -*- coding: utf-8 -*-


from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, current_app, request, url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
from . import login_manager, db
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from app.exceptions import ValidationError

class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80
	
class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
	timestamp = db.Column(db.DateTime, default = datetime.now)

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(64), unique = True)
	default = db.Column(db.Boolean, default = False, index = True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User', backref = 'role', lazy = 'dynamic')
	
	def __repr__(self):
		return '<Role %r>' % self.name
		
	@staticmethod
	def insert_roles():
		roles = {
			'User' : (Permission.FOLLOW | 
					Permission.COMMENT | 
					Permission.WRITE_ARTICLES, True),
			'Moderator' : (Permission.FOLLOW | 
							Permission.COMMENT | 
							Permission.WRITE_ARTICLES | 
							Permission.MODERATE_COMMENTS, False),
			'Administrator' : (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name = r).first()
			if role is None:
				role = Role(name = r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()
		
class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	email = db.Column(db.String(64), unique = True, index = True)
	username = db.Column(db.String(64), unique = True, index = True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default = False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default = datetime.now)
	last_seen = db.Column(db.DateTime(), default = datetime.now)
	avatar_hash = db.Column(db.String(32))
	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')     #author替代Post中的author_id  直接post.author = user
	followed = db.relationship('Follow', foreign_keys = [Follow.follower_id], 
								backref = db.backref('follower', lazy = 'joined'), 
								lazy = 'dynamic', cascade = 'all, delete-orphan')             #关注着   user.followed.all()  返回所有关注用户
	followers = db.relationship('Follow', foreign_keys = [Follow.followed_id], 
									backref = db.backref('followed', lazy = 'joined'), 
									lazy = 'dynamic', cascade = 'all, delete-orphan')			#被关注者  user.followers.all()  返回所有关注我用户
	comments = db.relationship('Comment', backref = 'author', lazy = 'dynamic')
	
	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permissions = 0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(default = True).first()
		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
				
	def __repr__(self):
		return '<User %r>' % self.username
		
	def ping(self):
		self.last_seen = datetime.now()
		db.session.add(self)
		db.session.commit()
		
	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')
		
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
		
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
		
	def generate_confirmation_token(self, expiration = 3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.id})
		
	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		db.session.commit()
		return True
		
	def generate_reset_token(self, expiration = 3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'reset': self.id})
		
	def resetpass(self, token, newpass):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('reset') != self.id:
			return False
		self.password = newpass
		db.session.add(self)
		db.session.commit()
		return True
		
	def generate_changeemail_token(self, newemail, expiration = 3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'change': self.id, 'newemail': newemail})
		
	def changemail(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('change') != self.id:
			return False
		self.email = data.get('newemail')
		self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
		db.session.add(self)
		db.session.commit()
		return True
		
	def can(self, permissions):
		return self.role is not None and (self.role.permissions & permissions) == permissions
		
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)
		
	def gravatar(self, size = 100, default = 'identicon', rating = 'g'):
		if request.is_secure:
			url = 'https://secure.gravatar.com/avatar'
		else:
			url = 'http://www.gravatar.com/avatar'
		if self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
			db.session.add(self)
			db.session.commit()
		hash = self.avatar_hash
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url = url, hash = hash, size = size, default = default, rating = rating)
		
	@staticmethod
	def generate_fake(count = 100):
		from sqlalchemy.exc import  IntegrityError
		from random import seed
		import forgery_py
		
		seed()
		for i in range(count):
			u = User(email = forgery_py.internet.email_address(),
					 username = forgery_py.internet.user_name(True),
					 password = forgery_py.lorem_ipsum.word(),
					 confirmed = True,
					 name = forgery_py.name.full_name(),
					 location = forgery_py.address.city(),
					 about_me = forgery_py.lorem_ipsum.sentence(),
					 member_since = forgery_py.date.date(True))
			db.session.add(u)
			try:
				db.session.commit()
			except IntegrityError:
				db.session.rollback()
				
	def follow(self, user):
		if not self.is_following(user):    #表示没有关注该用户   进行关注操作
			f = Follow(follower = self, followed = user)
			db.session.add(f)
			db.session.commit()
			
	def unfollow(self, user):     #如果已经关注该用户  就可以进行取消关注操作
		f = self.followed.filter_by(followed_id = user.id).first()
		if f:
			db.session.delete(f)
			db.session.commit()
	
	def is_following(self, user):          #查看是否已经关注该用户   没有关注返回False
		return self.followed.filter_by(followed_id = user.id).first() is not None
		
	def is_followed_by(self, user):     #如果已经被该用户关注  返回True
		return self.followers.filter_by(follower_id = user.id).first() is not None
		
	@property
	def followed_posts(self):
		return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)
		
	def generate_auth_token(self, expiration):
		s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
		return s.dumps({'id': self.id})
		
	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])
		
	def to_json(self):
		json_user = {
			'url' : url_for('api.get_user', id = self.id, _external = True),
			'username' : self.username,
			'member_since' : self.member_since,
			'last_seen' : self.last_seen,
			'posts' : url_for('api.get_user_posts', id = self.id, _external = True),
			'followed_posts' : url_for('api.get_user_followed_posts', id = self.id, _external = True),
			'post_count' : self.posts.count()
		}
		return json_user
		
class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index = True, default = datetime.now())
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))     #一般不用author_id   用上面users的author
	body_html = db.Column(db.Text)
	comments = db.relationship('Comment', backref = 'post', lazy = 'dynamic')
	
	@staticmethod
	def generate_fake(count = 100):
		from random import seed, randint
		import forgery_py
		
		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0, user_count - 1)).first()
			p = Post(body = forgery_py.lorem_ipsum.sentences(randint(1, 3)), 
						timestamp = forgery_py.date.date(True), 
						author = u)
			db.session.add(p)
			db.session.commit()
			
	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2', 'h3', 'p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format = 'html'), tags = allowed_tags, strip = True))
		
	def to_json(self):
		json_post = {
			'url' : url_for('api.get_post', id = self.id, _external = True),
			'body' : self.body,
			'body_html' : self.body_html,
			'timestamp' : self.timestamp,
			'author' : url_for('api.get_user', id = self.author_id, _external = True),
			'comments' : url_for('api.get_post_comments', id = self.id, _external = True),
			'comment_count' : self.comments.count()
		}
		return json_post
		
	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not hava a body')
		return Post(body = body)
		
class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index = True, default = datetime.now)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
	
	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
		target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format = 'html'), tags = allowed_tags, strip = True))
		
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
	
class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False
		
	def is_administrator(self):
		return False
		
login_manager.anonymous_user = AnonymousUser
db.event.listen(Post.body, 'set', Post.on_changed_body)
db.event.listen(Comment.body, 'set', Comment.on_changed_body)