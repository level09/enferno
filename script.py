from flask.ext.script import Command, prompt
from flask.ext.security.script import CreateUserCommand, AddRoleCommand
from user.models import Role

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
