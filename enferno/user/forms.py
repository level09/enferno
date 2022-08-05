from flask_security.forms import RegisterForm
from wtforms import StringField



class ExtendedRegisterForm(RegisterForm):
    name = StringField('Full Name')





class UserInfoForm():
    pass

