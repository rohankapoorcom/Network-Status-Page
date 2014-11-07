from flask import render_template

from status import app

import status

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/now_playing/')
def now_playing():
    videos = status.modules['plex'].get_currently_playing_videos()
    return render_template('now_playing.html', videos=videos)
