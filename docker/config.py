# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Jade Tree Configuration
JADETREE_APP_MODE = 'personal'

# Session and Token Keys (development - change for production !!)
APP_SESSION_KEY = 'jadetree-docker-session-key'
APP_TOKEN_KEY = 'jadetree-docker-token-key'

# Development Server Settings
DB_DRIVER = 'postgresql'
DB_HOST = 'db'
DB_PORT = 5432
DB_NAME = 'jadetree'
DB_USERNAME = 'jadetree'
DB_PASSWORD = 'jadetree'

# OpenAPI Swagger UI
OPENAPI_JSON_PATH = 'openapi-spec.json'
OPENAPI_URL_PREFIX = '/'
OPENAPI_SWAGGER_UI_PATH = '/swagger-ui'
OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

# SMTP Server Disabled
MAIL_ENABLED = False

# Logging Configuration
LOGGING_DEST = 'wsgi'
LOGGING_LEVEL = 'debug'
LOGGING_FORMAT = '[%(asctime)s] [%(remote_addr)s - %(url)s] %(levelname)s in %(module)s: %(message)s'
LOGGING_BACKTRACE = False

# Server User Information
SERVER_MODE = 'personal'
