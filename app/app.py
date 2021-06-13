# Aplikasi utama (server Flask)

from flask import Flask
from routes import site
from database import db, run
import os

# app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.register_blueprint(site)

# Konfigurasi koneksi database
DB_LOC = {
	'user': "informa",
	'pw':   "informa",
	'db':   "informa",
	'host': "localhost",
	'port': "5432"
}

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_LOC["user"]}:{DB_LOC["pw"]}@{DB_LOC["host"]}:{DB_LOC["port"]}/{DB_LOC["db"]}'

db.init_app(app)

if __name__ == '__main__':
	app.run()
