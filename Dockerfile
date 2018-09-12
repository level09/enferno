FROM python:2.7-slim

MAINTAINER Nidal Alhariri "nidal@level09.com"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev apt-utils libjpeg62-turbo-dev libzip-dev libxml2-dev libssl-dev libffi-dev libxslt1-dev  libncurses5-dev python-setuptools libpq-dev git

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENV FLASK_APP=run.py
ENV C_FORCE_ROOT="true"


RUN echo 'alias act="source env/bin/activate"' >> ~/.bashrc
RUN echo 'alias ee="export FLASK_APP=run.py && export FLASK_DEBUG=0"' >> ~/.bashrc



CMD [ "uwsgi", "--http", "0.0.0.0:5000", \
               "--protocol", "uwsgi", \
               "--wsgi", "run:app" ]

