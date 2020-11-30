Jade Tree Backend
=================

Backend API server for the [Jade Tree](https://jadetree.io) budgeting platform.
The API server is a [Flask](https://flask.palletsprojects.com/en/1.1.x/) which
interfaces to an [SQLalchemy](https://www.sqlalchemy.org/) database. Full
documentation is coming soon.

Quick Start
-----------

Install [Docker](https://www.docker.com/) and
[Docker Compose](https://docs.docker.com/compose/install/) for your platform.
Then run the following commands to clone the Jade Tree repository and run a
local instance of Jade Tree on your machine. Note that the database migration
only has to be done once to set up a fresh database or to upgrade a database to
the latest schema.

```sh
$ git clone https://github.com/asymworks/jadetree-backend.git jadetree
$ docker-compose -f jadetree/docker-compose.yml up -d
$ docker-compose -f jadetree/docker-compose.yml \
    exec backend /home/jadetree/docker-entry.sh db upgrade
```

Then access the Jade Tree instance at http://localhost:8733

Installation
------------

Coming Soon

Contribute
----------

- Issue Tracker: https://github.com/asymworks/jadetree-backend/issues
- Source Code: https://github.com/asymworks/jadetree-backend

API Documentation
-----------------

Coming Soon

License
-------

The project is licensed under the BSD license.
