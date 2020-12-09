# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

#: Jade Tree Application Entry Point for Flask Socket.io Server

from .factory import create_app
from .socketio import socketio
app = create_app()

socketio.run(app)
