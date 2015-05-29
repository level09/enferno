#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import MigrateCommand
from flask.ext.security.script import CreateUserCommand, AddRoleCommand, RemoveRoleCommand,ActivateUserCommand, DeactivateUserCommand
from script import InstallCommand, ResetUserCommand
from app import create_app

from settings import DevConfig, ProdConfig

#local settings should be ignored by git
try:
    from local_settings import LocalConfig
except ImportError:
    LocalConfig = None


if os.environ.get("ENFERNO_ENV") == 'prod':
    app = create_app(ProdConfig)
elif LocalConfig :
    app = create_app(LocalConfig)
else:
    app = create_app(DevConfig)

manager = Manager(app)


def _make_context():
    """Return context dict for a shell session so you can access
    app  default.
    """
    return {'app': app}


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))

manager.add_command('create_user', CreateUserCommand())
manager.add_command('add_role', AddRoleCommand())
manager.add_command('remove_role', RemoveRoleCommand())
manager.add_command('deactivate_user', DeactivateUserCommand())
manager.add_command('activate_user', ActivateUserCommand())
manager.add_command('reset_user', ResetUserCommand())
manager.add_command('install',InstallCommand())


if __name__ == '__main__':
    manager.run()
