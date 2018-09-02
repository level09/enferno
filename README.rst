Project Enferno (SQL Branch)
==================

A framework for the next decade, this is a collection of cutting-edge libraries and tools based on Flask framework.

http://enferno.io

To learn more about the framework and its use cases, you can follow my articles on Medium :

http://medium.com/@level09/

Tutorials
-------------

* First steps: create your first website with Enferno : https://medium.com/project-enferno/moonwalking-with-project-enferno-402937628745
* Customize your website : https://medium.com/project-enferno/moonwalking-with-project-enferno-part-2-9a23d39af55a
* Create a simple blog in 5 minutes: https://medium.com/project-enferno/create-a-simple-blog-in-5-min-using-project-enferno-be359ae77788?source=1
* Create a comic website with Enferno in 7 min: https://medium.com/project-enferno/create-a-comic-website-in-7-min-using-project-enferno-6c838c1e2742?source=1
* How to use background tasks and Mail in Enferno : https://medium.com/project-enferno/create-your-first-minion-with-project-enferno-f7884aa95443?source=1
* Deploy your Enferno project on Ubuntu in a minute: https://medium.com/project-enferno/tip-deploy-enferno-framework-on-ubuntu-with-a-single-command-cc1a596ec3f7
* How to deploy Enferno on Heroku: https://medium.com/project-enferno/deploy-your-enferno-website-on-heroku-for-free-810326f0aaa
* YOOO: a url shortener built with Enferno: https://medium.com/project-enferno/introducing-yooo-a-url-shortener-api-based-on-enferno-framework-823bdc2afa05?source=1


Prerequisites
-------------
 
* Redis
* Python Imaging (jpeg/png) support if you would like to work with images
* (Optional) Node.js and npm (for front-end stuff)

Quickstart
----------
::

    $ git clone git@github.com:level09/enferno.git
    
    $ cd enferno 
    
    $ virtualenv env
    
    $ source env/bin/activate 
    
    $ pip install -r requirements.txt

    $ npm install

Edit the settings.py and change the values to suit your needs, sepcifically you can change Flask security settings, security keys, Mysql settings,and Flask mail.

After that, you should create your admin user, run the following command:
::

    $ export FLASK_APP=run.py
    $ flask create_db
    $ flask install 

and follow the instructions, this will create your first user and first admin role.




to run the system, you can use a management command:

    $ flask run

Then 


    $ gulp
    

Features
--------
- Flask based
- Fully working user registration and authentication + user roles via Flask security
- Memory caching via Redis and Flask cache
- Command line scripting via Flask Script (will be replaced by "click" in the next release)
- Automatic assets bundling and minification via Flask assets
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
- `Mongoengine <http://mongoengine.org/>`_
- `Flask WTF <https://flask-wtf.readthedocs.org/en/latest/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_
- `Redis <http://redis.io/>`_
- `Flask Mail <https://pythonhosted.org/flask-mail/>`_
- `Flask Documentation <http://flask.pocoo.org/docs/>`_
- `Celery Task Queue <http://www.celeryproject.org/>`_


License
-------

MIT licensed.

