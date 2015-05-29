from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.widgets import TextInput


'''
class MyForm(Form):
    field = StringField('MyLabel',validators=[DataRequired,],widget=TextInput())
'''