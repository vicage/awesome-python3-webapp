# -*- coding: utf-8 -*-

from flask import Flask, current_app, request, url_for
from ..app_sqlalchemy import Postzzzx

def forbidden(message):
	response = jsonify({'error': 'forbidden', 'message': message})
	response.status_code = 403
	return response
	
@api.errorhandler(ValidationError)
def validation_error(e):
	return bad_request(e.args[0])
	
@api.route('/posts/', methods = ['POST'])
def new_post():
	post = Post.from_json(request.json)
	post.author = g.current_user
	db.session.add(post)
	db.session.commit()
	return jsonify(post.to_json())