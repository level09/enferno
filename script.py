from flask.ext.script import Command, prompt, Option
from flask.ext.security.script import CreateUserCommand, AddRoleCommand
from flask_security.utils import encrypt_password
from user.models import Role, User

class InstallCommand(Command):

    def run(self, **kwargs):
        #check if admin exists
        a = Role.objects.filter(name='admin').first()
        if a == None:
            Role(name='admin').save()
            u = prompt('Admin Email?',default='admin@enferno.io')
            p = prompt('Admin Password (min 6 characters)?',default='enferno')
            CreateUserCommand().run(email=u,password=p,active=1)
            AddRoleCommand().run(user_identifier=u,role_name='admin')
        else:
            print 'Seems like an Admin is already installed'



class ResetUserCommand(Command):
    option_list = (
        Option('-e', '--email', dest='email', default=None),
        Option('-p', '--password', dest='password', default=None),
    )
    def run(self, **kwargs):
        try:
            pwd = encrypt_password(kwargs['password'])
            User.objects(email=kwargs['email']).first().update(set__password=pwd)
        except Exception, e:
            print ('Error resetting user password: %s' % e)

