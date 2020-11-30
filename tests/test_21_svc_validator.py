# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import pytest
import re

from jadetree.exc import ConfigError
from jadetree.service.validator import RegexValidator, EmailValidator, \
    HasLowerCaseValidator, HasUpperCaseValidator, HasNumberValidator, \
    LengthValidator


def test_regex_validator():
    '''
    Regular Expression Validator should match and search strings using
    regular expressions.
    '''
    rev1 = RegexValidator(r'[a-z0-9]{4,8}', re.I, mode='match')
    rev2 = RegexValidator(r'[a-z0-9]{4,8}', re.I, mode='search')

    assert rev1('jadetree') is not None
    assert rev1('jad3tr33') is not None
    assert rev1('jade') is not None
    assert rev1('jadetree99') is not None
    assert rev2('jadetree99') is not None
    assert rev2('jadetree, but with more awesome') is not None

    with pytest.raises(ValueError):
        rev1('jt')
        rev1('44')
        rev1('jade+tre')
        rev2('jt')
        rev2('55')
        rev2('ja+de+tr+ee')


def test_regex_custom_exc():
    '''
    Validators can raise custom exception classes for interoperability
    '''
    rev1 = RegexValidator(r'^[a-z0-9]{4,8}$', exc_class=ConfigError)

    assert rev1('jadetree') is not None
    with pytest.raises(ConfigError):
        rev1('jadetree99')


def test_regex_custom_msg():
    '''
    Validators can raise custom exception messages
    '''
    rev1 = RegexValidator(r'^[a-z0-9]{4,8}$', message='Fail!')

    assert rev1('jadetree') is not None
    with pytest.raises(ValueError, match='Fail!'):
        rev1('jadetree99')


def test_regex_bad_mode():
    '''Regex Validator mode must be 'match' or 'search' '''
    with pytest.raises(ValueError, match='"match" or "search"'):
        RegexValidator(r'^[a-z0-9]{4,8}$', mode='infer')


def test_email_validator():
    '''Email Validator matches most sane email-ish strings'''
    emv = EmailValidator()

    assert emv('jadetree@jadetree.io') is not None
    assert emv('jadetree+inbox@jt.jt') is not None
    assert emv('jadetree.lastname@long.dotted.domain.name') is not None

    with pytest.raises(ValueError):
        emv('jadetree but like better@jadetree.io')
        emv('admin@localhost')


def test_password_validators():
    '''
    Password Validators ensure lower-case, upper-case, and numeric
    characters are present
    '''
    pw1 = 'aGood1shP4ssw0rd'
    pw2 = 'nouppercasel3tters'
    pw3 = 'N0L0W3RC453'
    pw4 = 'ALackOfNumbers'

    assert HasLowerCaseValidator()(pw1) is not None
    assert HasLowerCaseValidator()(pw2) is not None
    assert HasLowerCaseValidator()(pw4) is not None

    assert HasUpperCaseValidator()(pw1) is not None
    assert HasUpperCaseValidator()(pw3) is not None
    assert HasUpperCaseValidator()(pw4) is not None

    assert HasNumberValidator()(pw1) is not None
    assert HasNumberValidator()(pw2) is not None
    assert HasNumberValidator()(pw3) is not None

    with pytest.raises(ValueError):
        HasUpperCaseValidator()(pw2)
        HasLowerCaseValidator()(pw3)
        HasNumberValidator()(pw4)


def test_length_validator():
    '''String Length Validator should check strings for proper length'''
    lv1 = LengthValidator(min=8, max=12)
    lv2 = LengthValidator(min=32, exc_class=ConfigError)
    lv3 = LengthValidator(max=2, message='Needs to be short!')
    lv4 = LengthValidator()

    assert lv1('hunter22')
    assert lv2('a-really-long-string-like-an-encryption-key')
    assert lv3('ab')
    assert lv4('a')
    assert lv4('validator')
    assert lv4('which matches literally any string')

    with pytest.raises(ValueError, match='Invalid Value'):
        lv1('2short')
        lv1('too long of a string')

    with pytest.raises(ConfigError):
        lv2('this key isn\'t long enough')

    with pytest.raises(ValueError, match='Needs to be short!'):
        lv3('too long')
