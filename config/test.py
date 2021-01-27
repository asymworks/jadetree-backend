# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Default Jade Tree Test Configuration
SERVER_NAME = 'test.jadetree.local'

# Session and Token Keys
APP_SESSION_KEY = 'jadetree-test-session-key'
APP_TOKEN_KEY = 'jadetree-test-token-key'

APP_TOKEN_ISSUER = 'urn:jadetree.test'
APP_TOKEN_AUDIENCE = 'urn:jadetree.test'
APP_TOKEN_VALIDITY = 7200

# Development Database Settings (overridden by PyTest app_config Fixture)
DB_DRIVER = 'sqlite'
DB_FILE = 'jadetree-test.db'

# Mail Configuration
MAIL_ENABLED = True
MAIL_SERVER = 'localhost'
MAIL_SENDER = 'test@localhost'
MAIL_SUPPRESS_SEND = True

# Frontend Configuration
FRONTEND_HOST = 'http://localhost'
FRONTEND_LOGIN_PATH = '/login'
FRONTEND_LOGO_PATH = '/logo.png'
FRONTEND_REG_CONFIRM_PATH = '/register/confirm'
FRONTEND_REG_CANCEL_PATH = '/register/cancel'
FRONTEND_REG_RESEND_PATH = '/register/resend'

# Email Site Information
SITE_ABUSE_MAILBOX = 'abuse@localhost'
SITE_HELP_MAILBOX = 'help@localhost'
