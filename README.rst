Pyweek.org website
==================

This website runs the pyweek.org challenge.


Developing
----------

Database
''''''''

The production site runs against a PostgreSQL database. You can run one of
these using Docker for development purposes::

    docker run --name pyweek-postgresql postgres:latest

You will need to create an account and database on the new host. To do this you
will need the PostgreSQL ``psql`` command to be installed. Create a database
like this::

    psql (9.5.12, server 10.3 (Debian 10.3-1.pgdg90+1))
    WARNING: psql major version 9.5, server major version 10.
	     Some psql features might not work.
    Type "help" for help.

    postgres=# create database pyweek;
    CREATE DATABASE
    postgres=# \d
    No relations found.
    postgres=# CREATE USER pyweek WITH PASSWORD 'hunter2';
    CREATE ROLE
    postgres=# DROP DATABASE pyweek;
    DROP DATABASE
    postgres=# create database pyweek with owner pyweek;
    CREATE DATABASE
    postgres=# \q

You will need to put the IP address of this service into you settings; you can
obtain this with::

    docker inspect pyweek-postgresql

Environment
'''''''''''

How to set up a PyWeek-like site:

1. Create a virtualenv
2. Install ``requirements.txt`` and ``requirements-dev.txt``
3. Create a local settings file based on the template given in
   ``dev_settings_example.py``.


Running a dev server
''''''''''''''''''''

To run the dev server, use::

    django-admin.py runserver --settings=dev_settings --pythonpath=.
