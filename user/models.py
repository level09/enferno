from extensions import db
from flask.ext.security import UserMixin, RoleMixin
from extensions import bcrypt
import datetime


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80,unique=True)
    description = db.StringField(max_length=255)


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

    def is_active(self):
        return True

    def __unicode__(self):
        return '%s' % self.id

    def set_password(self, password):
        print '----------------- setting ---------------------'
        self.password = bcrypt.generate_password_hash(password)


    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return "%s %s %s" % (self.username, self.id, self.email)


    def get_id(self):
        return unicode(self.id)

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at', 'email', 'username'],
        'ordering': ['-created_at']
    }


