# Fungsi-fungsi yang digunakan dalam manajemen database

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# function untuk mempermudah ekseksusi SQL query
def run(sql, **args):
	return db.engine.execute(
		db.text(sql),
		args
	)
