"""Contains the Flask views"""

from flask import render_template

from status import app

import status

@app.route('/')
def home():
    """Loads the network status page"""
    return render_template('index.html')

@app.route('/now_playing/')
def now_playing():
    """Renders the now playing portion of the network status page"""
    videos = status.modules['plex'].get_currently_playing_videos()
    return render_template('now_playing.html', videos=videos)
