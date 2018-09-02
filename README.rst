Project Enferno (SQL Branch)
==================

A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework.

http://enferno.io

To learn more about the framework and its use cases, you can follow my articles on Medium :

http://medium.com/@level09/




Prerequisites
-------------

* Redis
* Postgresql (Default database) sqlite can be used for dev
* Python Imaging (jpeg/png) support if you would like to work with images


Quickstart
----------
::

    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt



Edit the settings.py and change the values to suit your needs, specifically you can change Flask security settings, security keys, Redis DB, Mysql settings, and Flask mail.

After that, you should create your admin user, run the following command:
::

    $ export FLASK_APP=run.py
    $ flask create_db
    $ flask install 

and follow the instructions, this will create your first user and first admin role.




to run the system, you can use a management command:

    $ flask run


Features
--------
- Flask based
- Fully working user registration and authentication + user roles via Flask security
- Memory caching via Redis and Flask cache
- Command line scripting via Click
- Relational database support with sql alchemy ORM
- Background tasks via Celery
- Email integration via Flask Mail
- Best practices by utilizing Flask blueprints and development/production configuration


Showcase
--------
Some of the websites running on Enferno: 

- `DUKES Hotel <http://dukeshotel.com>`_ 
- `Dubaiz Properties <http://dubaiz.com>`_ 
- `Bistro Des Arts <http://bistrodesarts.ae>`_ 
- `Seven Tides <http://seventides.com>`_ 
- `Anantara Residences <http://anantararesidences.com>`_ 


Inspiration & Credits
---------------------

- `Cookiecutter Flask <https://github.com/sloria/cookiecutter-flask>`_
- `Flask Security <https://pythonhosted.org/Flask-Security/>`_
- `Flask WTF <https://flask-wtf.readthedocs.org/en/latest/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_
- `Redis <http://redis.io/>`_
- `Flask Mail <https://pythonhosted.org/flask-mail/>`_
- `Flask Documentation <http://flask.pocoo.org/docs/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_


License
-------

MIT licensed.

