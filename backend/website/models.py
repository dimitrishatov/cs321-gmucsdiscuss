from . import db
from sqlalchemy.sql import func

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name=db.Column(db.String(10))