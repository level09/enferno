from flask_admin.contrib.mongoengine import ModelView
from user.models import User
from flask_security import current_user
from flask_admin import expose, BaseView


class UserView(ModelView):
    column_list = ['created_at', 'email','active','confirmed_at','last_login_at','roles']
    form_columns = ['email','roles']
    def is_accessible(self):
        return current_user.has_role('admin')



class RoleView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')
