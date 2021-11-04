# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

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

# Frontend Configuration
FRONTEND_HOST = 'http://localhost:8733'
FRONTEND_LOGIN_PATH = '/login'
FRONTEND_LOGO_PATH = '/apple-touch-icon.png'
FRONTEND_REG_CONFIRM_PATH = '/register/confirm'
FRONTEND_REG_CANCEL_PATH = '/register/cancel'
FRONTEND_REG_RESEND_PATH = '/register/resend'

# Site Email Configuration
SITE_ABUSE_MAILBOX = 'abuse@localhost'
SITE_HELP_MAILBOX = 'info@localhost'

# Server User Information
SERVER_MODE = 'personal'
