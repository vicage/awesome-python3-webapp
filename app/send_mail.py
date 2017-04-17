# -*- coding: utf-8 -*-


from flask import Flask
from flask.ext.mail import Mail, Message
from flask import render_template
from threading import Thread

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.exmail.qq.com'
app.config['MAIL_USERNAME'] = 'kaijie.yang@karakal.com.cn'
app.config['MAIL_PASSWORD'] = '1234567Ykj'
app.config['FLASK_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASK_MAIL_SENDER'] = 'Flasky Admin <kaijie.yang@karakal.com.cn>'
mail = Mail(app)


def send_sync_email(app, msg):
	with app.app_context():
		mail.send(msg)

def send_email(to, subject, template, **kwargs):
	msg = Message(app.config['FLASK_MAIL_SUBJECT_PREFIX'] + subject, sender = app.config['FLASK_MAIL_SENDER'], recipients = [to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)
	thr = Thread(target = send_sync_email, args = [app, msg])
	thr.start()
	return thr