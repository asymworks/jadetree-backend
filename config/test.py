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
