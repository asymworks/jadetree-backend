"""Jade Tree Custom Marshmallow Validators.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

import typing

from marshmallow import ValidationError
from marshmallow.validate import Validator

from jadetree.service.validator import (
    HasLowerCaseValidator,
    HasNumberValidator,
    HasUpperCaseValidator,
    LengthValidator,
)


class JTPasswordValidator(Validator):
    """Jade Tree Password Validator."""

    validators = [
        LengthValidator(
            min=8,
            message='Password must be at least 8 characters long',
        ),
        HasLowerCaseValidator(
            message='Password must contain a lower-case letter',
        ),
        HasUpperCaseValidator(
            message='Password must contain an upper-case letter',
        ),
        HasNumberValidator(
            message='Password must contain a number',
        ),
    ]

    default_message = (
        'Password must be at least 8 characters long and contain an upper-case '
        'letter, a lower-case letter, and a number'
    )

    def __init__(self, *, error: typing.Optional[str] = None):
        """Initialize the Password Validator."""
        self.error = error or self.default_message  # type: str

    def _format_error(self, value) -> typing.Any:
        return self.error.format(input=value)

    def __call__(self, value) -> typing.Any:
        """Validate a Password."""
        message = self._format_error(value)
        for val in self.validators:
            try:
                val(value)
            except ValueError:
                # Re-Raise with better message
                raise ValidationError(message)

        return value
