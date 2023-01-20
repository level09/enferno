FROM ubuntu:latest


RUN apt update -y && apt install -yq  python3-dev python3-pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENV FLASK_APP=run.py
ENV C_FORCE_ROOT="true"
ENV SQLALCHEMY_DATABASE_URI="postgresql://enferno:verystrongpass@postgres/enferno"
ENV CELERY_BROKER_URL="redis://:verystrongpass@redis:6379/10"
ENV CELERY_RESULT_BACKEND="redis://:verystrongpass@redis:6379/11"
ENV SESSION_REDIS="redis://:verystrongpass@redis:6379/1"

RUN echo 'alias act="source env/bin/activate"' >> ~/.bashrc
RUN echo 'alias ee="export FLASK_APP=run.py && export FLASK_DEBUG=0"' >> ~/.bashrc



CMD [ "uwsgi", "--http", "0.0.0.0:5000", \
               "--protocol", "uwsgi", \
               "--master", \
               "--wsgi", "run:app" ]

