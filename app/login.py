# Fungsi-fungsi yang digunakan dalam login

from flask import session

def login_user(user):
	session['user_id'] = user.id

def get_logged_in_user():
	if 'user_id' in session:
		return session['user_id']
	else:
		return None

def logout_user():
	session.pop('user_id', None)
