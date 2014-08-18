Project Enferno
==================

A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework.

http://enferno.io

Prerequisites
-------------

You will need Mongodb and Redis installed.

Quickstart
----------
::

    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env --distribute --no-site-packages 
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt 

After that, you should create your first user: 

::

    $ ./manage.py create_user -e email@example.com -p yourpassword 
    
Assign an 'Admin' role to your username: 

::

    $ ./manage.py add_role -u email@example.com -r admin
    

Edit the settings.py and change the settings to suit your needs, sepcifically you can change Flask security settings, security keys, Mongodb settings,and Flask mail.

to run the system, you can use a management command:
::

    $ ./manage.py server

Features
--------
- Flask based
- Jasny Bootstrap on the frontend
- Fully working user registration and authentication + user roles via Flask security and Flask Principal
- Memory caching via Redis and Flask cache
- Simple admin backend via Flask Admin
- Command line scripting via Flask Script (will be replaced by "click" in the next release)
- Automatic assets bundling and minification via Flask assets
- Mongodb and Mongoengine ORM
- Background tasks via Celery
- Email integration via Flask Mail
- Best practices by utilizing Flask blueprints and development/production configuration



Inspiration & Credits
---------------------

- `Cookiecutter Flask <https://github.com/sloria/cookiecutter-flask>`_
- `Flask Security <https://pythonhosted.org/Flask-Security/>`_
- `Mongoengine <http://mongoengine.org/>`_
- `Jasny Bootstrap <http://jasny.github.io/bootstrap/>`_
- `Flask WTF <https://flask-wtf.readthedocs.org/en/latest/>`_
- `Flask Admin <https://github.com/mrjoes/flask-admin/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_
- `Redis <http://redis.io/>`_
- `Flask Mail <https://pythonhosted.org/flask-mail/>`_
- `Flask Documentation <http://flask.pocoo.org/docs/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_


License
-------

MIT licensed.

