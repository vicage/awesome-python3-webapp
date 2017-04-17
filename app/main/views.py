# -*- coding: utf-8 -*-

from flask import render_template
from flask import redirect, url_for, session, flash, abort, request, current_app, make_response
from datetime import datetime
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..app_sqlalchemy import User, Role, Permission, Post, Comment
from flask.ext.login import login_user, logout_user, login_required, current_user
from ..decorators import admin_required, permission_required

@main.route('/', methods = ['GET', 'POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(body = form.body.data, author = current_user._get_current_object())
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type = int)
	show_followed = '1'
	if current_user.is_authenticated:
		show_followed = request.cookies.get('show_followed', '2')
	if show_followed == '2':
		query = current_user.followed_posts
	elif show_followed == '1':
		query = Post.query
	else:
		query = current_user.posts
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page, per_page = current_app.config['ALICY_POSTS_PER_PAGE'], error_out = False)
	posts = pagination.items
	return render_template('form.html', form = form, posts = posts, show_followed = show_followed, pagination = pagination)
	
@main.route('/user', methods = ['GET', 'POST'])
def login():
	return redirect(url_for('main.index'))
	
@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate( 
        page, per_page=current_app.config['ALICY_POSTS_PER_PAGE'], 
        error_out = False)
	posts = pagination.items
	return render_template('userinfo.html', user = user, posts = posts, pagination = pagination)
	
@main.route('/edit-profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		flash('修改完成')
		return redirect(url_for('main.user', username = current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form = form)
	
@main.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user = user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		db.session.commit()
		flash('该用户信息已经更新')
		return redirect(url_for('main.user', username = user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form = form, user = user)
	
@main.route('/post/<int:id>', methods = ['GET', 'POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body = form.body.data, post = post, author = current_user._get_current_object())
		db.session.add(comment)
		flash('你的评论已经提交')
		return redirect(url_for('main.post', id = post.id, page = -1))
	page = request.args.get('page', 1, type = int)
	if page == -1:
		page = (post.comments.count() -1) / current_app.config['ALICY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page = current_app.config['ALICY_COMMENTS_PER_PAGE'], error_out = False)
	comments = pagination.items
	return render_template('post.html', posts = [post], form = form, comments = comments, pagination = pagination)
	
@main.route('/edit/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('已经修改~！')
		return redirect(url_for('main.post', id = post.id))
	form.body.data = post.body
	return render_template('edit_post.html', form = form)
	
@main.route('/deleteindex/<int:id>')
@login_required
def deleteindex(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	else:
		db.session.delete(post)
		db.session.commit()
		flash('已经删除~！')
	return redirect(url_for('main.index'))
	
@main.route('/deleteuserinfo/<int:id>')
@login_required
def deleteuserinfo(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	else:
		db.session.delete(post)
		db.session.commit()
		flash('已经删除~！')
	return redirect(url_for('main.user', username = current_user.username))
	
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('该用户已经不存在')
		return redirect(url_for('main.index'))
	if current_user.is_following(user):
		flash('你已经关注此用户')
		return redirect(url_for('main.user', username = username))
	current_user.follow(user)
	flash('关注成功~!')
	return redirect(url_for('main.user', username = username))
	
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('该用户已经不存在')
		return redirect(url_for('main.index'))
	current_user.unfollow(user)
	flash('取消关注成功~!')
	return redirect(url_for('main.user', username = username))
	
@main.route('/follows/<username>')
def follows(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('该用户已经不存在')
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type = int)
	pagination = user.followers.paginate(
		page, per_page = current_app.config['ALICY_POSTS_PER_PAGE'], error_out = False)
	follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
	return render_template('followers.html', user = user, title = "被关注", endpoint = 'main.follows', pagination = pagination, follows = follows)
	
@main.route('/followed_by/<username>')
def followed_by(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('该用户已经不存在')
		return redirect(url_for('main.index'))
	page = request.args.get('page', 1, type = int)
	pagination = user.followed.paginate(
		page, per_page = current_app.config['ALICY_POSTS_PER_PAGE'], error_out = False)
	follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
	return render_template('followed_by.html', user = user, title = "我的关注", endpoint = 'main.followed_by', pagination = pagination, follows = follows)
	
@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('main.index')))
	resp.set_cookie('show_followed', '1', max_age = 30 * 24 * 60 * 60)
	return resp
	
@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('main.index')))
	resp.set_cookie('show_followed', '2', max_age = 30 * 24 * 60 * 60)
	return resp
	
@main.route('/myself')
@login_required
def show_myself():
	resp = make_response(redirect(url_for('main.index')))
	resp.set_cookie('show_followed', '3', max_age = 30 * 24 * 60 * 60)
	return resp
	
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type = int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page = current_app.config['ALICY_COMMENTS_PER_PAGE'], error_out = False)
	comments = pagination.items
	return render_template('moderate.html', comments = comments, pagination = pagination, page = page)
	
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('main.moderate', page = request.args.get('page', 1, type = int)))
	
@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('main.moderate', page = request.args.get('page', 1, type = int)))
	
