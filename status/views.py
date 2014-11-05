from status import app
from flask import render_template

import status
import json

@app.route('/')
def home():
    print(status.modules['plex'].get_currently_playing_videos())
    return render_template('index.html', message=status.modules['plex'].get_token())

@app.route('/now_playing/')
def now_playing():
    return json.dumps(status.modules['plex'].get_currently_playing_videos())
