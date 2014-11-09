"""Contains the Flask views"""

from flask import render_template

from status import app

import status

@app.route('/')
def home():
    """Loads the network status page"""
    return render_template('index.html')

def now_playing():
    """Renders the now playing portion of the network status page"""
    videos = status.modules['plex'].get_currently_playing_videos()
    if not videos:
        return False
    return render_template('now_playing.html', videos=videos)

def recently_released():
    """Renders the recently released portion of the network status page"""
    videos = status.modules['plex'].get_recently_released_videos()
    return render_template('recently_released.html', videos=videos)

def forecast():
    """Renders the forecast portion of the network status page"""
    weather = status.modules['forecast'].get_forecast()
    return render_template('forecast.html', weather=weather)

@app.template_filter('strftime')
def _jinja2_filter_datetimeformat(value, format='%I:%M %p'):
    """Allows Jinja templates to reformat datetime objects"""
    return value.strftime(format)
