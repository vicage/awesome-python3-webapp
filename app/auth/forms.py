# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..app_sqlalchemy import User
from flask.ext.login import current_user

class LoginForm(Form):
	email = StringField('邮箱地址：', validators = [Required(), Length(1, 64), Email()])
	password = PasswordField('密码：', validators = [Required()])
	remember_me = BooleanField('记住我')
	submit = SubmitField('登录')
	
class RegistrationForm(Form):
	email = StringField('邮箱地址：', validators = [Required(), Length(1, 64), Email()])
	username = StringField('用户名：', 
		validators = [Required(), Length(1, 64), 
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
		'用户名必须是字母、数字、下划线或点号~!')])
	password = PasswordField('密码：', validators = [Required(), EqualTo('password2', message = '密码前后不一致~!!')])
	password2 = PasswordField('确认密码：', validators = [Required()])
	submit = SubmitField('完成')
	def validate_email(self, field):        # validate_XX    XX为上面的表单组件名字   相当于增加验证条件   不需要调用该函数  会自动执行
		if User.query.filter_by(email = field.data).first():
			raise ValidationError('该邮箱已经注册~!')
	def validate_username(self, field):
		if User.query.filter_by(username = field.data).first():
			raise ValidationError('该用户名已经被占用~!')
			
class ModifyPassForm(Form):
	oldpass = PasswordField('输入旧密码：', validators = [Required()])
	newpass = PasswordField('新密码：', validators = [Required(), EqualTo('newpassre', message = '密码前后不一致~!!')])
	newpassre = PasswordField('确认新密码：', validators = [Required()])
	submit = SubmitField('完成')
	
class ResetPassEmailForm(Form):
	email = StringField('注册邮箱地址：', validators = [Required(), Length(1, 64), Email()])
	submit = SubmitField('确认')
	def validate_email(self, field):
		if not User.query.filter_by(email = field.data).first():
			raise ValidationError('该邮箱未注册..')
			
class ResetPassForm(Form):
	#email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
	newpass = PasswordField('新密码：', validators = [Required(), EqualTo('password2', message = '密码前后不一致~!!')])
	password2 = PasswordField('确认新密码：', validators = [Required()])
	submit = SubmitField('完成')
	# def validate_email(self, field):
		# if not User.query.filter_by(email = field.data).first():
			# raise ValidationError('该邮箱未注册..')
			
class ChangeEmailForm(Form):
	email = StringField('输入现在邮箱号：', validators = [Required(), Length(1, 64), Email()])
	newemail = StringField('输入新邮箱：', validators = [Required(), Length(1, 64), Email()])
	submit = SubmitField('完成')
	def validate_email(self, field):
		if current_user.email != field.data:
			raise ValidationError('邮箱输入错误、不能修改邮箱')
	def validate_newemail(self, field):
		if User.query.filter_by(email = field.data).first() is not None:
			raise ValidationError('该邮箱已经注册')