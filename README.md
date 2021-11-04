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
$ docker-compose -f jadetree/docker-compose.yml restart backend
```

Then access the Jade Tree instance at http://localhost:8733

Installation
------------

Coming Soon

Developing on Apple M1
----------------------

Jade Tree is developed on an Apple M1 machine; however, the Python cryptography
library (specifically the libcffi dependency) is not yet shipping arm64 wheels,
so the backend will not run without additional help. The solution found at
https://stackoverflow.com/questions/66035003/installing-cryptography-on-an-apple-silicon-m1-mac
seems to work, and is what is recommended here. Prerequisites are having Homebrew
installed in the default `/opt/homebrew` location and libffi installed via
`brew install libffi`. Use this process to initialize a new development setup:

```shellscript
# Clone new repository:
$ git clone https://github.com/asymworks/jadetree-backend.git
$ cd jadetree-backend

# Reinstall cffi:
$ poetry install
$ poetry run python -m pip uninstall cffi cryptography
$ LDFLAGS=-L$(brew --prefix libffi)/lib CFLAGS=-I$(brew --prefix libffi)/include poetry run python -m pip install cffi --no-binary :all:
$ poetry run python -m pip install cryptography

# Ensure tests pass:
$ make test
```

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
