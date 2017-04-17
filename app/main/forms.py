# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField 
from wtforms.validators import Required, Length, Email, ValidationError, Regexp
from ..app_sqlalchemy import Role, User
from flask.ext.pagedown.fields import PageDownField

class NameForm(Form):
	name = StringField('What is your name?', validators = [Required()])
	submit = SubmitField('Submit')
	
class EditProfileForm(Form):
	name = StringField('真实姓名', validators = [Length(0, 64)])
	location = StringField('地址', validators = [Length(0, 64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('完成')
	
class EditProfileAdminForm(Form):
	email = StringField('邮箱地址', validators = [Required(), Length(1, 64), Email()])
	username = StringField('用户名', validators = [Required(), Length(1, 64), Regexp('^[A-Za-z]{4,12}\_[A-Za-z0-9]{4,12}$', 0, '用户名格式不对')])
	confirmed = BooleanField('是否已激活')
	role = SelectField('角色', coerce = int)
	name = StringField('真实姓名', validators = [Length(0, 64)])
	location = StringField('地址', validators = [Length(0, 64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('提交')
	
	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user
		
	def validate_email(self, field):
		if field.data != self.user.email and User.query.filter_by(email = field.data).first():
			raise ValidationError('该邮箱号已经注册')
			
	def validate_username(self, field):
		if field.data != self.user.username and User.query.filter_by(username = field.data).first():
			raise ValidationError('该用户名已经存在')
			
class PostForm(Form):
	body = PageDownField('你想要写点什么？', validators = [Required()])
	submit = SubmitField('提交')
	
class CommentForm(Form):
	body = StringField('', validators = [Required()])
	submit = SubmitField('提交')
			
			