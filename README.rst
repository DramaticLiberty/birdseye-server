birdseye-server
===============

The Flask-based, PostgreSQL backed REST API to capture observations on the migration patterns of endangered species

Installation
============

TODO

Development
===========

PostgreSQL database creation & setup
------------------------------------

Create the birdseye database, user and set it up with the GIS extension.

.. code:: bash

   sudo apt-get install postgresql-9.6
   sudo apt-get install postgresql-9.6-postgis-2.3 postgresql-contrib-9.6 libpq-dev postgis

   sudo -i -u postgres

   # Create a new user (if a user named 'birdseye' does not exist already)
   createuser -P birdseye (password birdseye)

   createdb -E UTF8 -O birdseye birdseye
   createlang plpgsql birdseye
   psql -d birdseye -c "CREATE EXTENSION postgis;"
   psql -d birdseye -c "CREATE EXTENSION postgis_topology;"
   psql birdseye
   grant all on database birdseye to "birdseye";
   grant all on spatial_ref_sys to "birdseye";
   grant all on geometry_columns to "birdseye";
   \q

Python virtualenv setup
-----------------------

Requires python 3.5 (and above) and python-pew to manage the python virtualenv.

.. code:: bash

   pew new birdseye
   pip install -r dev-requirements.txt

MacOS X (tested in El Capitan)
------------------------------

Assuming homebrew is used, assuming pip, pew and pythonz are installed.

Install python and friends:

.. code:: bash

          # follow instructions from pythonz to use openssl:
          xcode-select --install
          brew install openssl
          export CPPFLAGS="-I/usr/local/opt/openssl/include"
          export LDFLAGS="-L/usr/local/opt/openssl/lib"
          pythonz install 3.5.3


Download and install the Postgres app from http://postgresapp.com/ and start a postgres server 9.6.

Setup a database:

.. code:: bash

          brew install postgis
          createdb -E UTF8 -O $USER birdseye
          createlang plpgsql birdseye
          psql -d birdseye << EOT
          CREATE EXTENSION postgis;
          CREATE EXTENSION postgis_topology;
          grant all on database birdseye to \"$USER\";
          grant all on spatial_ref_sys to \"$USER\";
          grant all on geometry_columns to \"$USER\";
          EOT

Virtual env setup:

.. code:: bash

          pew new --python=$(pythonz locate 3.5.3) birdseye
          pip install -r dev-requirements.txt


Testing
-------

.. code:: bash

   birdseye --help
   birdseye reset_tables
   birdseye test
   birdseye runserver

Production
----------

In production gunicorn with gevent is used, will bind to a unix socket created in the same dir from where the server is lauched.

.. code:: bash

   birdseye runproduction

Changelog
=========

* 0.0.1 - Initial release
