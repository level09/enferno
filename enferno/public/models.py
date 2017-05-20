import datetime
from enferno.extensions import db


class Timestamp(object):
    created_at = db.DateTimeField(default=datetime.utcnow())
    updated_at = db.DateTimeField()

#your models can go here
'''
class MyModel(db.Document, Timestamp):
    my_id = db.IntField()
    my_field = db.StringField()

'''