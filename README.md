Project Enferno 
=================

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Flevel09%2Fenferno.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Flevel09%2Fenferno?ref=badge_shield)

A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework, that will help build any website or web app (SAAS) extremely fast !

http://enferno.io


![Project Enferno](http://www.enferno.io/blog/content/images/size/w2000/2019/04/127.0.0.1_5000_--1-.png)


What's New
==================
- Docker! you can now test the framework directly using docker-compose 
- Removed MongoDB in favour of Postgresql (or Mysql/sqlite) with sqlalchemy. 
- No more front-end bundlers (feel free to integrate your own : webpack, gulp, parcel, etc ..) 
- Upgraded all python libraries (also based on flask 1.x)
- More tutorials will be coming soon. 

Prerequisites
-------------

* Redis
* Postgresql (Default database) sqlite can be used for dev
* Python Imaging (jpeg/png) support if you would like to work with images


Quickstart
----------

The fastest and easiest way to run the system is by using docker-compose:

::

    $ git clone git@github.com:level09/enferno.git

    $ cd enferno

    $ docker-compose up

https://asciinema.org/a/219755


Alternatively, you can install it locally: 

::

    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt



Edit the settings.py and change the values to suit your needs, specifically you can change Flask security settings, security keys, Redis DB, Mysql settings, and Flask mail.

If you are installing Enferno locally, you will also need to replace "redis" and "postgres" with "localhost" in connection strings. 

After that, you should create your admin user, run the following command:
::

    $ export FLASK_APP=run.py
    $ flask create-db
    $ flask install 

and follow the instructions, this will create your first user and first admin role.



to run the system, you can use a management command:

    $ flask run


Features
--------
- Flask based
- Fully working user registration and authentication + user roles via Flask security
- Memory caching via Redis and Flask caching
- Command line scripting via Click
- Relational database support with sql alchemy ORM
- Background tasks via Celery
- Email integration via Flask Mail
- Files are structured based on best practices by utilizing Flask blueprints and development/production configuration


Showcase
--------
Some of the websites running on Enferno: 
- Seven Tides <http://seventides.com>
- DUKES Hotel <http://dukeshotel.com>


Inspiration & Credits
---------------------

- Cookiecutter Flask <https://github.com/sloria/cookiecutter-flask>
- Flask Security <https://pythonhosted.org/Flask-Security/>
- Flask WTF <https://flask-wtf.readthedocs.org/en/latest/>
- Celery Task Queue <http://www.celeryproject.org/>
- Redis <http://redis.io/>
- Flask Mail <https://pythonhosted.org/flask-mail/>
- Flask Documentation <http://flask.pocoo.org/docs/>
- Celery Task Queue <http://www.celeryproject.org/>


License
-------

MIT licensed.

