Project Enferno
==================

A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework.

http://enferno.io

To learn more about the framework and its use cases, you can follow my articles on Medium :

http://medium.com/@level09/


Prerequisites
-------------

* MongoDB 
* Redis
* Python Imaging (jpeg/png) support if you would like to work with images


Quickstart
----------
::

    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt 

After that, you should create your admin user, run the following command:
::

    $ ./manage.py install
    
and follow the instructions


Edit the settings.py and change the settings to suit your needs, sepcifically you can change Flask security settings, security keys, Mongodb settings,and Flask mail.

to run the system, you can use a management command:
::

    $ ./manage.py server


Features
--------
- Flask based
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

