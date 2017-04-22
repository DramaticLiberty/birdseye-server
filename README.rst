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

.. codeblock
sudo apt-get install postgresql libpq-dev
sudo -i -u postgres

# Create a new user (if a user named 'birdseye' does not exist already)
createuser -P birdseye (password birdseye)

createdb -E UNICODE -O birdseye birdseye
createlang plpgsql gis
psql -d birdseye -f /usr/share/postgresql-9.5-postgis/lwpostgis.sql
psql -d birdseye -f /usr/share/postgresql-9.5-postgis/spatial_ref_sys.sql

# Grant permissions to user 'birdseye' on the new database
psql birdseye
grant all on database birdseye to "birdseye";
grant all on spatial_ref_sys to "birdseye";
grant all on geometry_columns to "birdseye";
\q
..


Python virtualenv setup
-----------------------

TODO

Testing
-------

TODO


Changelog
=========

* 0.0.1 - Initial release
