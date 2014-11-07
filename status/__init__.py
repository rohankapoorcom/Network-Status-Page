from flask import Flask
from flask_util_js import FlaskUtilJs
from flask_socketio import SocketIO

app = Flask(__name__)
fujs = FlaskUtilJs(app)
socketio = SocketIO(app)
config = {}
modules = {}

import status.views
