from flask_admin.contrib.mongoengine import ModelView
from user.models import User

class UserView(ModelView):
    
    column_list = ['created_at', 'email','active','confirmed_at','last_login_at','roles']
    form_columns = ['email','roles']



class RoleView(ModelView):
	pass
