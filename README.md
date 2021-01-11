Project Enferno 
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework, that will help build any website or web app (SAAS) extremely fast !

http://enferno.io




What's New
==================
- Vue integration!  Vue is now bundled by default with a clean default structure to build and integrate npm modules. 
- Parcel bundler is now available by default (optional to use).  
- Docker! you can now test the framework directly using docker-compose 
- Upgraded all python libraries 
 

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

If you are installing Enferno locally, you will also need to replace "redis" and "postgres" with "localhost" in connection strings. 

After that, you should create your admin user, run the following command:
::

    $ export FLASK_APP=run.py
    $ flask create-db
    $ flask install 

and follow the instructions, this will create your first user and first admin role.



to run the system, you can use a management command:

    $ flask run

to use Vue and Parcel bundler for development: 
```
$ npm install -g parcel-bundler
$ npm install
$ npm run watch
```
to build for production run:
 
    $ npm run build 

Favicons Generator
----------------- 
To use the favicons generator, just replace `enferno/src/favicons/enferno.svg` with your own logo and run: 
```
$ npm run favicons 
```
A full set of favicons will be generated inside `enferno/static/favicons/` directory. 

feel free to modify the script inside `favicons.js` to fit your needs. 

Using Docker
------------



    $ git clone git@github.com:level09/enferno.git

    $ cd enferno

    $ docker-compose up

https://asciinema.org/a/219755


Running Celery
-------------

`celery -A enfenro.tasks worker `

you can add `-b` to activate Celery heartbeat (periodic tasks) 

A sample task that runs within the app context has been prepared for you within the `enfenro/tasks/__init__.py` file, this is helpful if you have background tasks that interact with your SQLAlchemy models. 




Features
--------
- Based on Flask. 
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
- Seven Tides <https://seventides.com>
- Shamal Communications <https://www.shamalcomms.com/>
- Mixed CRM <https://www.mixedcrm.com>
- DUKES Hotel <https://dukeshotel.com>


Inspiration & Credits
---------------------

- Cookiecutter Flask <https://github.com/sloria/cookiecutter-flask>
- Flask Security <https://github.com/Flask-Middleware/flask-security/>
- Flask WTF <https://flask-wtf.readthedocs.org/en/latest/>
- Celery Task Queue <http://www.celeryproject.org/>
- Redis <http://redis.io/>
- Flask Mail <https://pythonhosted.org/flask-mail/>
- Flask Documentation <http://flask.pocoo.org/docs/>


License
-------

MIT licensed.

