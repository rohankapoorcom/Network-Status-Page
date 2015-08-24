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


def services():
    """Renders the services portion of the network status page"""
    service_list = status.modules['services'].get_status()
    return render_template('services.html', service_list=service_list)


@app.template_filter('strftime')
def _jinja2_filter_datetimeformat(value, format='%I:%M %p'):
    """Allows Jinja templates to reformat datetime objects"""
    return value.strftime(format)


@app.template_filter('button_style')
def _jinja2_filter_button_style(value):
    """Formats the button style for templates"""
    return 'success' if value else 'warning'


@app.template_filter('icon_style')
def _jinja2_filter_icon_style(value):
    """Formats the icon style for templates"""
    return 'ok' if value else 'remove'

@app.template_filter('service_style')
def _jinja2_filter_service_style(value):
    """Formats the service style for templates"""
    return 'Online' if value else 'Offline'
