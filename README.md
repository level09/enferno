Project Enferno 
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/enferno/badge/?version=latest)](https://enferno.readthedocs.io/en/latest/?badge=latest)



A framework for the next decade, this assemblage of state-of-the-art libraries and tools, grounded on the Flask framework, facilitates the rapid construction of any website or web-based application (SAAS) with remarkable speed!


![alt Enferno Demo](https://github.com/level09/enferno/blob/master/docs/enferno-hero.gif)

![alt Users Management](https://github.com/level09/enferno/blob/master/docs/users-management.jpg)

![alt Roles Management](https://github.com/level09/enferno/blob/master/docs/roles-management.jpg)

http://enferno.io




What's New
==================
- Users and Roles Management Dashboard 
- Eliminated JavaScript build scripts and complex configurations
- Incorporated Vue3, Vuetify3, and axios through client-side JavaScript without the necessity of build tools
- Implemented the latest flask-security templates and views utilizing sleek Vuetify templates (Material Design)
- Streamlined configurations through .env, bypassing the need for distinct classes per environment
- Cleanup and removed favicon generator 
Features
--------
- An opinionated Flask-based framework designed with pre-integrated utilities and adherence to best practices. 
- Fully functional user registration and authentication systems, alongside user role management through Flask security.
- Redis integration: capable of facilitating Flask caching, as well as handling various in-memory, queuing, and key-value operations as needed.
- Command line scripting facilitated by Click, empowering you to create your own commands with ease.
- Support for relational databases through the utilization of SQLAlchemy ORM.
- Efficient management of background tasks using Celery.
- Smooth email integration facilitated through Flask Mail.
- Incorporation of the Vue3 framework and Vuetify3, providing an aesthetically pleasing UI grounded in material design principles. 
 

Prerequisites
-------------
* Python
* Redis
* Nginx (needed for production deployment)

Quickstart
----------


    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt



Modify the settings.py file to tailor it to your requirements, particularly tweaking Flask security settings, security keys, Redis DB configurations, MySQL settings, and Flask mail options.

For a local Enferno installation, remember to replace "redis" and "postgres" with "localhost" in the connection strings. 

Subsequently, duplicate or rename the file (.env-sample) to (.env), and tweak the settings therein. Following this, proceed to run 

    flask create-db
    flask install 

and follow the directions, which will establish your database tables, and set up the initial admin user and role.

to run the system, you can use the following management command:

    $ flask run



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


Showcase
--------
Some of the websites running on Enferno: 
- Seven Tides <https://seventides.com>
- Mixed CRM <https://www.mixedcrm.com>
- DUKES Hotel <https://dukeshotel.com>


Inspiration & Credits
---------------------

- Cookiecutter Flask <https://github.com/sloria/cookiecutter-flask>
- Flask Security <https://github.com/Flask-Middleware/flask-security/>
- Redis <http://redis.io/>
- Flask Mail <https://pythonhosted.org/flask-mail/>
- Flask Documentation <http://flask.pocoo.org/docs/>


License
-------

MIT licensed.

