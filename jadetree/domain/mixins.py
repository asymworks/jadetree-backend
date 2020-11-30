# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from arrow import Arrow, utcnow
from dataclasses import dataclass


@dataclass
class NotesMixin:
    '''
    Domain Model Mixin Class for objects with Notes

    .. :py:attr:: notes
        :property:

        Adds a column to the database object with type
        :py:class:`~sqlalchemy.types.Text` which is intended for the user to
        add notes associated with the object.

    '''
    notes: str = None


@dataclass
class TimestampMixin:
    '''
    Domain Model Mixin Class for Timestamped Objects

    .. :py:attr:: created_at
        :property:

        Adds a ``created_at`` column to the database object with type
        :py:class:`~jadetree.models.types.ArrowType`

    .. :py:attr:: modified_at
        :property:

        Adds a ``modified_at`` column to the database object with type
        :py:class:`~jadetree.models.types.ArrowType`
    '''
    created_at: Arrow = utcnow()
    modified_at: Arrow = None

    def set_modified(self):
        self.modified_at = utcnow()
