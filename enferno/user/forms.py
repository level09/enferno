from flask_security.forms import ConfirmRegisterForm
from wtforms import StringField
from wtforms.validators import Required

class ExtendedRegisterForm(ConfirmRegisterForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')


