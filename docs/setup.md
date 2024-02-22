# Setting up

## Clone the repo

```
$ git clone https://github.com/level09/enferno.git 
$ cd enferno

```

## Initialize a virtualenv

```
$ python3 -m venv env
$ source env/bin/activate
```


## Add Environment Variables

copy .env-sample to .env and modify the settings to your needs.

you can generate a secret key using the following command:



```
import secrets
secrets.token_urlsafe(16)
```



**Note: do not include the `.env` file in any commits. This should remain private.**

## Install the dependencies

```
$ pip install -r requirements.txt
```

## Other dependencies for running locally

You need [Redis](http://redis.io/), Optional (If you don't want to use sqlite ) [PostgresQL](https://www.postgresql.org/),  installed to run the app locally.



**Redis:**

_Mac (using [homebrew](http://brew.sh/)):_

```
$ brew install redis
```

_Linux:_

```
$ sudo apt-get install redis-server
```

 **PostgresQL**

_Mac (using homebrew):_

```
brew install postgresql
```

_Linux (Ubuntu):_

```
sudo apt-get install postgresql
```

## Create the database (if you are using Postgres)

```
$ createdb <your-database-name>
$ flask create-db
```

## Install the first admin

```
$ flask install 
```


## Running the app

```
$ source env/bin/activate
$ flask run
```

## Running Celery

```
$ celery -A enferno.tasks worker 
```
