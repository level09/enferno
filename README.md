Project Enferno
=================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/enferno/badge/?version=latest)](https://enferno.readthedocs.io/en/latest/?badge=latest)

This collection of modern libraries and tools, built on top of the Flask framework, allows you to quickly create any
website or web-based application (SaaS) with impressive speed. The framework is highly opinionated and comes with
pre-configured user accounts, authentication, and a management dashboard out of the box. It also integrates seamlessly
with Vue 3 and Vuetify 3 on the frontend, enabling the rapid development of interactive and visually appealing user
interfaces.

![alt Enferno Demo](https://github.com/level09/enferno/blob/master/docs/enferno-hero.gif)

![alt Users Management](https://github.com/level09/enferno/blob/master/docs/users-management.jpg)

![alt Roles Management](https://github.com/level09/enferno/blob/master/docs/roles-management.jpg)

http://enferno.io

Enferno Framework Update: OpenAI Integration 🚀
==============
I'm excited to introduce OpenAI integration within the Enferno framework! This feature allows for rapid generation of
Flask Views, Templates, and Models using just natural language. Streamline your development process by creating base
code samples that can be customized to fit your needs, saving you valuable time.

New Commands:

- flask generate-model: Instantly generate models with natural language.
- flask generate-dashboard: Create dashboards by simply describing your requirements.
- flask generate-api: Speed up API development with verbal descriptions.

This update is aimed at boosting your productivity by reducing development time and making the coding process more
intuitive. Experience the next level of efficient programming with Enferno and OpenAI!




Features
==================

- A Flask-based framework with built-in tools and best practices.
- User registration, login, and role management features.
- Redis integration for caching and handling in-memory operations.
- Easy command line scripting with Click.
- Support for relational databases using SQLAlchemy.
- Background task management with Celery.
- Easy email sending with Flask Mail.
- Beautiful user interface using Vue3 and Vuetify3 frameworks.
- Internationalization support using Flask-Babel for multi-language apps

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

Modify the settings.py file to tailor it to your requirements, particularly tweaking Flask security settings, security
keys, Redis DB configurations, MySQL settings, and Flask mail options.

For a local Enferno installation, remember to replace "redis" and "postgres" with "localhost" in the connection strings.

Subsequently, duplicate or rename the file (.env-sample) to (.env), and tweak the settings therein. Following this,
proceed to run

    flask create-db
    flask install 

and follow the directions, which will establish your database tables, and set up the initial admin user and role.

to run the system, you can use the following management command:

    $ flask run

Running Celery
-------------

`celery -A enfenro.tasks worker `

you can add `-b` to activate Celery heartbeat (periodic tasks)

A sample task that runs within the app context has been prepared for you within the `enfenro/tasks/__init__.py` file,
this is helpful if you have background tasks that interact with your SQLAlchemy models.



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

