from flask_admin.contrib.mongoengine import ModelView
from user.models import User

class UserView(ModelView):
    can_create = False
    column_list = ['created_at', 'email','active','confirmed_at','last_login_at']
    form_columns = ['email']



