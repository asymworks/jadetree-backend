#!/bin/bash
set -e

export FLASK_APP=jadetree.factory
export FLASK_ENV=production
export JADETREE_CONFIG=${JADETREE_CONFIG:-/home/jadetree/config.py}
export JADETREE_PORT=${JADETREE_PORT:-5000}

source venv/bin/activate

if [ "$1" = 'jadetree' ]; then
  exec gunicorn -b :${JADETREE_PORT} --access-logfile - --error-logfile - jadetree.wsgi:app
fi

if [ "$1" = 'db' ]; then
  if [ "$2" = 'downgrade' ]; then
    exec flask db downgrade
  else
    exec flask db upgrade
  fi

  exit 0
fi

exec "$@"
