# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

__all__ = (
    'AuthError',
    'ConfigError',
    'DomainError',
    'Error',
    'JwtInvalidTokenError',
    'JwtExpiredTokenError',
    'JwtPayloadError',
    'NoResults',
    'Unauthorized',
)


class Error(Exception):
    '''Base Class for Jade Tree Errors'''
    default_code = 500

    def __init__(self, *args, **kwargs):
        self.status_code = kwargs.pop('status_code', self.__class__.default_code)
        super(Error, self).__init__(*args, **kwargs)


class AuthError(Error):
    '''Base Class for Jade Tree Authentication/Authorization Errors'''
    pass


class Unauthorized(AuthError):
    '''Exception raised when access to a resource is not allowed'''
    pass


class ConfigError(Error):
    '''
    Exception raised for invalid or missing configuration values.

    .. attribute:: config_key
        :type: str

        Configuration key which is missing or invalid

    '''
    def __init__(self, *args, config_key=None):
        super(ConfigError, self).__init__(*args)
        self.config_key = config_key


class DomainError(Error):
    '''Base Class for Jade Tree Domain Logic Errors'''
    pass


class JwtInvalidTokenError(Error):
    '''
    Exception raised for invalid or missing JSON Web Token data. This
    exception class is raised during :meth:`AuthService.decodeJwt` processing
    and wraps exceptions from the underlying :mod:`PyJwt <jwt>` framework.

    .. attribute:: jwt_exception
        :type: Exception

        Original exception raised by :func:`jwt.decode`

    .. attribute:: token_key
        :type: str

        Payload or Header field name which is missing or invalid

    '''
    def __init__(self, jwt_exception, *args, token_key=None):
        if len(args) == 0:
            super(JwtInvalidTokenError, self).__init__(
                '{jwt_exc_class}({jwt_exc_msg})'.format(
                    jwt_exc_class=jwt_exception.__class__.__name__,
                    jwt_exc_msg=str(jwt_exception)
                )
            )
        else:
            super(JwtInvalidTokenError, self).__init__(*args)

        self.jwt_exception = jwt_exception
        self.token_key = token_key


class JwtExpiredTokenError(Error):
    '''
    Exception raised for expired JSON Web Tokens
    '''
    pass


class JwtPayloadError(Error):
    '''
    Exception raised for invalid or missing JSON Web Token payload fields.
    This exception class is raised during application-specific processing of
    the token payloads, unlike :class:`JwtTokenError` which relates to the
    JWT specification.

    .. attribute:: payload_key
        :type: str

        Payload field name which is missing or invalid

    '''
    def __init__(self, *args, payload_key=None):
        super(JwtPayloadError, self).__init__(*args)
        self.payload_key = payload_key


class MultipleResults(Error):
    '''
    Exception raised when multiple results were found for a query when exactly
    one result was expected.
    '''
    pass


class NoResults(Error):
    '''
    Exception raised when no results were found for a query when exactly one
    result was expected.
    '''
    pass
