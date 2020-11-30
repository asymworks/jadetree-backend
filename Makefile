
export FLASK_APP := jadetree.factory

shell serve db-init db-migrate db-upgrade db-downgrade db-populate : export FLASK_ENV := development
shell serve db-init db-migrate db-upgrade db-downgrade db-populate : export JADETREE_CONFIG := ../config/dev.py
coverage coverage-html coverage-report test test-wip test-x : export FLASK_ENV := production

shell-psql serve-psql export : export FLASK_ENV := development
shell-psql serve-psql export : export JADETREE_CONFIG := ../config/dev-docker.py

coverage :
	poetry run coverage run --source=jadetree -m pytest tests

coverage-html :
	poetry run coverage html -d .htmlcov && open .htmlcov/index.html

coverage-report :
	poetry run coverage report -m

db-init :
	poetry run flask db init

db-migrate :
	poetry run flask db migrate

db-upgrade :
	poetry run flask db upgrade

db-downgrade :
	poetry run flask db downgrade

db-populate :
	$(RM) jadetree-dev.db
	poetry run flask db upgrade
	poetry run python scripts/load_core_db.py
	poetry run python scripts/load_test_transactions.py

docs :
	$(MAKE) -C docs html

docs-clean :
	$(MAKE) -C docs clean

docs-serve :
	poetry run sphinx-autobuild docs docs/_build/html --no-initial -B -s 1

export :
	poetry run flask export budgets 1 > export.qif
	poetry run flask export payees 1 >> export.qif
	poetry run flask export accounts 1 >> export.qif

lint :
	poetry run flake8

requirements.txt : poetry.lock
	poetry export -f requirements.txt -o requirements.txt

requirements-dev.txt : poetry.lock
	poetry export --dev -f requirements.txt -o requirements-dev.txt

shell :
	poetry run flask shell

shell-psql :
	poetry run flask shell

serve :
	poetry run flask run -h 0.0.0.0

serve-psql :
	poetry run flask run -h 0.0.0.0

sqlalchemy :
	/usr/local/Cellar/sqlite/3.32.1/bin/sqlite3 jadetree-dev.db

test :
	poetry run python -m pytest tests

test-x :
	poetry run python -m pytest tests -x

test-wip :
	poetry run python -m pytest tests -m wip

all: serve

.PHONY: coverage coverage-html coverage-report \
	db-init db-migrate db-upgrade db-downgrade db-populate \
	docs docs-clean docs-serve \
	lint shell serve shell-psql serve-psql \
	test test-wip test-x
