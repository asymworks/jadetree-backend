# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import re

__all__ = (
    'RegexValidator',
    'EmailValidator',
    'HasLowerCaseValidator',
    'HasUpperCaseValidator',
    'HasNumberValidator',
    'LengthValidator',
)


class LengthValidator(object):
    '''
    Validates that a string input has a length between a specified minimum and
    maximum. If either value is None, it is not evaluated. This class allows
    the user to specify  exception class to be raised in case of failure.
    This will allow the validator to be used by both WTForms and Marshmallow.

    :param min:
        Minimum string length, or None to allow any length below the maximum

    :param max:
        Maximum string length, or None to allow any length above the minimum

    :param message:
        Error message to raise in case of a validation error.

    :param exc_class:
        Exception class to be raised in case of a validation error.

    '''
    default_message = 'Invalid Value'
    default_exc_class = ValueError

    def __init__(self, min=0, max=None, message=None, exc_class=None):
        self.min = min
        self.max = max
        self.message = message
        self.exc_class = exc_class

    def __call__(self, value, message=None, exc_class=None):
        sl = len(value)
        if self.min and sl < self.min or self.max and sl > self.max:
            if message is None:
                if self.message is None:
                    message = self.default_message
                else:
                    message = self.message

            if exc_class is None:
                if self.exc_class is None:
                    exc_class = self.default_exc_class
                else:
                    exc_class = self.exc_class

            raise exc_class(message)

        return True


class RegexValidator(object):
    '''
    Validates data against a user-provided regular expression.  Extends the
    WTForms :class:`~wtforms:validator.Regex` by allowing a search or an
    exact match, and also allows the user to specify the exception class to
    be raised in case of failure.  This will allow the validator to be used by
    both WTForms and Marshmallow.

    :param regex:
        The regular expression string to use. Can also be a compiled regular
        expression pattern.

    :param flags:
        The regular expression flags to use, for example re.IGNORECASE.
        Ignored if `regex` is not a string.

    :param message:
        Error message to raise in case of a validation error.

    :param exc_class:
        Exception class to be raised in case of a validation error.

    :param mode:
        Set to 'match' (default) or 'search'

    '''
    default_message = 'Invalid Value'
    default_exc_class = ValueError

    def __init__(self, regex, flags=0, message=None, exc_class=None,
                 mode='match'):
        if isinstance(regex, str):
            regex = re.compile(regex, flags)
        if mode.lower() not in ('match', 'search'):
            raise ValueError(
                'Regular Expression mode must be "match" or "search"'
            )
        self.regex = regex
        self.mode = mode.lower()
        self.message = message
        self.exc_class = exc_class

    def __call__(self, value, message=None, exc_class=None):
        value = value or ''
        if self.mode == 'match':
            rv = self.regex.match(value)
        else:
            rv = self.regex.search(value)

        if not rv:
            if message is None:
                if self.message is None:
                    message = self.default_message
                else:
                    message = self.message

            if exc_class is None:
                if self.exc_class is None:
                    exc_class = self.default_exc_class
                else:
                    exc_class = self.exc_class

            raise exc_class(message)

        return rv


# Email and Password Validation Helpers
RE_EMAIL = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$', re.I)
RE_PW_UPPERCASE = re.compile(r'[A-Z]+')
RE_PW_LOWERCASE = re.compile(r'[a-z]+')
RE_PW_NUMERIC = re.compile(r'[0-9]+')


class EmailValidator(RegexValidator):
    '''
    Extends :class:`RegexValidator` to do a rough validation of an email
    address (mainly just that it contains an ``@`` sign and a domain name at
    with at least two parts).
    '''
    default_message = 'Invalid Email Address'
    default_exc_class = ValueError

    def __init__(self, message=None, exc_class=ValueError):
        super(EmailValidator, self).__init__(
            RE_EMAIL,
            message=message,
            exc_class=exc_class,
            mode='match'
        )


class HasUpperCaseValidator(RegexValidator):
    '''
    Extends :class:`RegexValidator` to validate that a password or other
    string has at least one upper-case letter.
    '''
    default_message = 'Must contain an upper-case letter'
    default_exc_class = ValueError

    def __init__(self, message=None, exc_class=ValueError):
        super(HasUpperCaseValidator, self).__init__(
            RE_PW_UPPERCASE,
            message=message,
            exc_class=exc_class,
            mode='search'
        )


class HasLowerCaseValidator(RegexValidator):
    '''
    Extends :class:`RegexValidator` to validate that a password or other
    string has at least one lower-case letter.
    '''
    default_message = 'Must contain a lower-case letter'
    default_exc_class = ValueError

    def __init__(self, message=None, exc_class=ValueError):
        super(HasLowerCaseValidator, self).__init__(
            RE_PW_LOWERCASE,
            message=message,
            exc_class=exc_class,
            mode='search'
        )


class HasNumberValidator(RegexValidator):
    '''
    Extends :class:`RegexValidator` to validate that a password or other
    string has at least one number.
    '''
    default_message = 'Must contain a number'
    default_exc_class = ValueError

    def __init__(self, message=None, exc_class=ValueError):
        super(HasNumberValidator, self).__init__(
            RE_PW_NUMERIC,
            message=message,
            exc_class=exc_class,
            mode='search'
        )
