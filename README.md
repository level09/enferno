Project Enferno 
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework, that will help build any website or web app (SAAS) extremely fast !

http://enferno.io




What's New
==================
- Better configuration management with python-dotenv support 
- Favicon generator: just put your logo in enferno/src/favicons dir and automatically generate all favicons adn presets for all platforms. 


Features
--------
- A Flask based opinionated framework with pre-installed batteries and best practices in mind.  
- Fully working user registration and authentication,  user roles via Flask security
- Redis: can be used for Flask caching, or any in-memory/queuing/key-value operations needed. 
- Command line scripting via Click, feel free to build your own commands easily. 
- Relational database support with sqlalchemy ORM 
- Background tasks via Celery
- Email integration via Flask Mail
- Vue framework and npm scripts with pre-configured asset bundling. 
- Sample Vue component (front-page) to help you get started. 

 

Prerequisites
-------------
* Python
* Redis
* Postgresql (Default database) sqlite can be used for dev
* Python Imaging (jpeg/png) support if you would like to work with images
* Nginx (needed for production deployment)

Quickstart
----------




    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt



Edit the settings.py and change the values to suit your needs, specifically you can change Flask security settings, security keys, Redis DB, Mysql settings, and Flask mail.

If you are installing Enferno locally, you will also need to replace "redis" and "postgres" with "localhost" in connection strings. 

After that, copy or rename the file (.env-sample) to (.env) and adjust the settings inside, then run 


    flask create-db
    flask install 

and follow the instructions, that will create your database tables, and  first admin user and role.



to run the system, you can use the following management command:

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


Running Celery
-------------

`celery -A enfenro.tasks worker `

you can add `-b` to activate Celery heartbeat (periodic tasks) 

A sample task that runs within the app context has been prepared for you within the `enfenro/tasks/__init__.py` file, this is helpful if you have background tasks that interact with your SQLAlchemy models. 



Using Docker
------------
Feel free to adjust Docker settings inside the docker-compose.yml and Dockerfile / .env file. 
then run: 

    $ docker-compose up

https://asciinema.org/a/219755

Looking for more? 
------------
check out [Anymal.io](https://anymal.io) which includes pre-configured Vuetify backend, User management/auth fully skinned 
based on Material Design, and pre-configured Stripe membership integration. 



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

