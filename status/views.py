"""Contains the Flask views"""

from flask import render_template, request, make_response

from status import app

import status


@app.route('/')
def home():
    """Loads the network status page"""
    return render_template('index.html')


@app.route('/image/')
def fetch_image():
    """Loads and returns the requested image"""
    url = request.args.get('image')
    req = status.modules['plex'].get_image_from_plex(url)
    response = make_response(req.content)
    response.headers['Content-Type'] = req.headers['Content-Type']
    return response


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


def bandwidth():
    """Renders the bandwidth portion of the network status page"""
    interfaces = status.modules['pfsense'].get_interfaces()
    return render_template('bandwidth.html', interfaces=interfaces)


@app.template_filter('strftime')
def _jinja2_filter_datetimeformat(value, format='%I:%M %p'):
    """Allows Jinja templates to reformat datetime objects"""
    return value.strftime(format)
