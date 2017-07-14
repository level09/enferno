from enferno.extensions import  db
from flask_security import UserMixin, RoleMixin
import datetime


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80,unique=True)
    description = db.StringField(max_length=255)

    def __unicode__(self):
        return '%s' % self.name


class User(UserMixin, db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)
    email = db.StringField(max_length=255, required=True)
    username = db.StringField(max_length=255, required=False)
    password = db.StringField(required=True)
    active = db.BooleanField(default=False)
    roles = db.ListField(db.ReferenceField(Role),default=[])
    #email confirmation
    confirmed_at = db.DateTimeField()
    #tracking
    last_login_at = db.DateTimeField()
    current_login_at = db.DateTimeField()
    last_login_ip = db.StringField()
    current_login_ip = db.StringField()
    login_count = db.IntField()

    def __unicode__(self):
        return '%s' % self.id

    def __repr__(self):
        return "%s %s %s" % (self.username, self.id, self.email)


    meta = {
        'allow_inheritance': True,
        'indexes': ['created_at', 'email', 'username'],
        'ordering': ['-created_at']
    }

