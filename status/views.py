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


def volumes():
    """Renders the volumes portion of the network status page"""
    volume_list = status.modules['freenas'].get_volumes()
    return render_template(
        'volumes.html',
        volume_list=volume_list,
        total_space_avail=status.modules['freenas'].get_total_avail(),
        total_space=status.modules['freenas'].get_total_space(),
        total_percent_used=status.modules['freenas'].get_percent_used()
    )


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


@app.template_filter('storage_percent_class')
def _jinja2_filter_storage_percent_class(value):
    """Formats the storage percentage class for templates"""
    value = int(value[:-1])
    if value < 95:
        return "progress-bar"
    elif value < 99:
        return "progress-bar progress-bar-warning"
    return "progress-bar progress-bar-danger"


@app.template_filter('storage_unit_value')
def _jinja2_filter_storage_unit_value(num, suffix='B'):
    """
    Formats storage units into human readable text
    from http://stackoverflow.com/a/1094933
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
