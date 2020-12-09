# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask import current_app, request
from flask_socketio import join_room, rooms

from jadetree.database import db
from jadetree.service import auth as auth_service
from jadetree.socketio import socketio


def handle_api_connection():
    try:
        token = request.args.get('access_token', None)
        if token is None or token == '':
            current_app.logger.warning('WebSockets connection request with no token')
            return False

        # Load the User from the Token
        user = auth_service.load_user_by_token(db.session, token)
        if user is None:
            current_app.logger.warning('WebSockets connection request for non-existant user')
            return False

        # Join the User's Room
        join_room(user.uid_hash)

        # Log Success
        current_app.logger.debug(
            'Opened WebSocket connection for {} in rooms {}'.format(
                user.email,
                ', '.join(rooms())
            )
        )

    except Exception as e:
        current_app.logger.exception(
            'WebSockets Connection Error (%s): %s',
            e.__class__.__name__,
            str(e)
        )
        return False


def init_api_socketio(ns):
    socketio.on_event('connect', handle_api_connection, namespace=ns)
