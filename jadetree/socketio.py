# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

from flask_socketio import SocketIO

socketio = SocketIO()

__all__ = ('socketio', 'init_socketio')


def init_socketio(app):
    '''Initialize the Web Socket Handler'''
    socketio.init_app(app, cors_allowed_origins='*')

    # Notify Initialization
    app.logger.debug('Web Sockets Initialized')

    # Return Success
    return True
