# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required
from . import auth
from .. import db
from ..app_sqlalchemy import User
from .forms import LoginForm, RegistrationForm, ModifyPassForm, ResetPassEmailForm, ResetPassForm, ChangeEmailForm
from ..send_mail import send_email
from flask.ext.login import current_user

@auth.route('/login', methods = ['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main.login'))
		flash('用户名错误或者密码错误')
	return render_template('auth/login.html', form = form)
	
@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('你已退出登录')
	return redirect(url_for('main.index'))
	
@auth.route('/register', methods = ['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email = form.email.data, 
					username = form.username.data,
					password = form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_email(user.email, 'confirm your account', 'auth/email/confirm', user = user, token = token)
		flash('激活邮件已经发送~！')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form = form)
	
@auth.route('/confirm/<token>')
def confirm(token):
	if not current_user.is_authenticated:
		flash('请先登录，再激活~')
		return redirect(url_for('auth.login'))
	if current_user.confirmed:
		return redirect(url_for('main.login'))
	if current_user.confirm(token):
		flash('已经激活账户~!')
	else:
		flash('暂时不能激活， 请重试~！')
	return redirect(url_for('main.login'))
	
@auth.before_app_request
def before_request():
	if current_user.is_authenticated:
		current_user.ping()
		if not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
			return redirect(url_for('auth.unconfirmed'))
		
@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.login'))
	return render_template('auth/unconfirmed.html')
	
@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_confirmation_token()
	send_email(current_user.email, 'confirm your account', 'auth/email/confirm', user = current_user, token = token)
	flash('新的激活邮件已经发送~！')
	return redirect(url_for('main.login'))
	
@auth.route('/modifypass', methods = ['GET', 'POST'])
@login_required
def modifypass():
	form = ModifyPassForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.oldpass.data):
			current_user.password = form.newpass.data
			db.session.add(current_user)
			db.session.commit()
			flash('密码已经更改成功')
			return redirect(url_for('main.login'))
		else:
			flash('原密码不正确~!')
	return render_template('auth/modifypass.html', form = form)
	
@auth.route('/resetpass_email', methods = ['GET', 'POST'])
def resetpass_email():
	form = ResetPassEmailForm()
	if not current_user.is_anonymous:
		return redirect(url_for('main.login'))
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		token = user.generate_reset_token()
		send_email(user.email, 'reset your password', 'auth/email/resetpass', user = user, email = form.email.data, token = token)
		flash('确认邮件已经发送到注册邮箱，请点击邮件链接完成密码重置')
		return redirect(url_for('main.index'))
	return render_template('auth/resetpass_email.html', form = form)
	
@auth.route('/resetpass/<token>/<email>', methods = ['GET', 'POST'])
def resetpass(token, email):
	form = ResetPassForm()
	if not current_user.is_anonymous:
		return redirect(url_for('main.login'))
	user = User.query.filter_by(email = email.replace('%40', '@')).first()
	if form.validate_on_submit():
		if user.resetpass(token, form.newpass.data):
			flash('密码已经更改成功')
			return redirect(url_for('auth.login'))
		#flash('邮箱不匹配，请重试')
	return render_template('auth/resetpass.html', form = form)
	
@auth.route('/changeemail_email', methods = ['GET', 'POST'])
@login_required
def changeemail_email():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		newemail = form.newemail.data
		token = current_user.generate_changeemail_token(newemail)
		send_email(newemail, 'change your email', 'auth/email/changeemail', user = current_user, token = token)
		flash('确认邮件已经发送到新邮箱，请点击邮件中链接完成后面操作')
		return redirect(url_for('main.index'))
	return render_template('auth/changeemail_email.html', form = form)
	
@auth.route('/changeemail/<token>', methods = ['GET', 'POST'])
@login_required
def changeemail(token):
	if current_user.changemail(token):
		flash('邮箱修改成功')
	else:
		flash('请求出错， 请重试~')
	return redirect(url_for('main.login'))