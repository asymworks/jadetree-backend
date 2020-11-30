# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

# Service Layer Utilities

import inspect
from jadetree.exc import DomainError, Unauthorized
from werkzeug.local import LocalProxy


def check_session(session):
    fn_name = inspect.currentframe().f_back.f_code.co_name
    if session is None:
        raise ValueError(
            'Session object must be provided to {}'.format(fn_name)
        )


def check_user(user, needs_profile=False):
    fn_name = inspect.currentframe().f_back.f_code.co_name
    if user is None:
        raise ValueError(
            'User must not be None in {}'.format(fn_name)
        )
    if not user.is_active:
        raise DomainError('User is not active in {}'.format(fn_name))
    if not user.id:
        raise ValueError(
            'User instance must have an id set in {}'.format(fn_name)
        )
    if needs_profile and not user.profile_setup:
        raise DomainError(
            'User profile must be set up for {}'.format(fn_name)
        )


def check_access(user, obj, user_fn=lambda o: o.user):
    fn_name = inspect.currentframe().f_back.f_code.co_name
    obj_cls = obj.__class__.__name__
    if isinstance(obj, LocalProxy):
        obj_cls = obj._get_current_object().__class__.__name__

    if user_fn(obj) != user:
        raise Unauthorized(
            'User is not authorized to access {} id {} in {}'.format(
                obj_cls,
                obj.id,
                fn_name
            )
        )
