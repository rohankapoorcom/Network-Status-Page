"""
Contains functions and classes needed for processing the Network Status Page
"""

from xml.etree import ElementTree
from flask import copy_current_request_context, url_for
from flask_socketio import emit
from datetime import datetime

from status import app, socketio, modules
from status.views import now_playing, recently_released, forecast

import requests
import grequests
import gevent
import forecastio

class Plex:
    """Contains the functionality needed to communicate with a Plex server"""
    _STATUS_URL = '/status/sessions'
    _LIBRARY_URL = '/library/sections'
    _RELEASED_URL = '/library/sections/{}/newest'

    def __init__(self, username, password, server_name, api_token_uri, **kwargs):
        """Initializes the Plex server communication"""
        self._username = username
        self._password = password
        self._server = server_name
        self._token_url = api_token_uri
        self.fetch_token()

    def fetch_token(self):
        """Fetch's the Plex authentication token"""
        headers = {
            'Content-Length' : 0,
            'X-Plex-Client-Identifier': __name__
        }

        tree = ElementTree.fromstring(
            requests.post(
                self._token_url,
                auth=(self._username, self._password),
                headers=headers
                ).content
            )

        self._payload = {'X-Plex-Token': tree.get('authenticationToken')}

    def process_currently_playing_video(self, unprocessed_video):
        """Returns a dictionary containing information regarding the provided video"""
        video = {}
        metadata_url = unprocessed_video.get('key')
        try:
            video['device'] = unprocessed_video.find('Player').get('title')
            video['state'] = unprocessed_video.find('Player').get('state')
            video['user'] = unprocessed_video.find('User').get('title')
        except AttributeError:
            # unprocessed_video is not currently being watched
            pass

        video_tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, metadata_url),
                params=self._payload
                ).content
            )

        metadata = video_tree.find('Video')

        try:
            duration = float(metadata.get('duration'))
            view_offset = float(metadata.get('viewOffset'))
            video['progress'] = '{0:.2f}'.format((view_offset / duration) * 100)
        except (AttributeError, TypeError):
            # unproccessed_video is not currently being watched
            pass

        video_type = metadata.get('type')
        video['type'] = video_type

        if (video_type == 'movie'):
            thumb = metadata.get('thumb')

            video['title'] = metadata.get('title')
            summary = metadata.get('summary')
            video['summary'] = (summary[:800] + '...') if len(summary) > 800 else summary

        elif (video_type == 'episode'):
            thumb = metadata.get('thumb') if not metadata.get('grandparentThumb') else metadata.get('grandparentThumb')

            video['title'] = metadata.get('grandparentTitle')
            video['episode_title'] = metadata.get('title')
            video['summary'] = metadata.get('summary')
            video['season'] = metadata.get('parentIndex')
            video['episode_number'] = metadata.get('index')

        video['artwork'] = url_for(
            'fetch_image',
            image=thumb
        )

        return video

    def get_currently_playing_videos(self):
        """
        Returns a list of dictionaries containing information about all
        currently playing videos
        """
        tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, Plex._STATUS_URL),
                params=self._payload
            ).content
        )

        videos = tree.findall('Video')
        if not videos:
            return []
        return [self.process_currently_playing_video(video) for video in videos]

    def get_libraries_to_scan(self):
        """Returns a list of urls of libraries to get recently playing videos"""
        section_tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, Plex._LIBRARY_URL),
                params=self._payload
            ).content
        )

        directories = section_tree.findall('Directory')
        return ['{}{}'.format(
            self._server,
            Plex._RELEASED_URL.format(
                directory.get('key'))
        ) for directory in directories]

    def get_recently_released_videos(self):
        """
        Returns a list of dictionaries containing information about all
        recently released videos
        """
        sections = self.get_libraries_to_scan()
        processed_videos = []
        for section in sections:
            video_tree = ElementTree.fromstring(
                requests.get(
                    section,
                    params=self._payload
                ).content
            )

            videos = video_tree.findall('Video')
            processed_videos.extend(self.process_currently_playing_video(video) for video in videos[:5])

        return processed_videos

    def get_image_from_plex(self, image_url):
        """
        Returns a raw response from a request to plex to fetch
        the image to be displayed
        """
        return requests.get(
            '{}{}'.format(self._server, image_url),
            params=self._payload
        )


class ForecastIO:
    """
    A Wrapper for the python-forecastio package allowing one time loading
    of the API key and latitude/longitude coordinates
    """

    def __init__(self, api_key, latitude, longitude, **kwargs):
        """Initializes an instance of the ForecastIO wrapper"""
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._forecast = forecastio.load_forecast(self._api_key, self._latitude, self._longitude)

    def get_direction(self, bearing):
        """Converts a bearing to written direction"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
        return directions[int(round(bearing/45))]

    def get_icon_code(self, icon):
        """Converts a weather icon to the character that represents it"""
        weather_icons = {
            'clear-day': 'B',
            'clear-night': 'C',
            'rain': 'R',
            'snow': 'W',
            'sleet': 'X',
            'wind': 'F',
            'fog': 'L',
            'cloudy': 'N',
            'partly-cloudy-day': 'H',
            'partly-cloudy-night': 'I'
        }

        return weather_icons[icon]

    def get_forecast(self):
        """
        Returns a dictionary containing the weather information we want to
        display
        """
        weather = {}
        current = self._forecast.currently().d
        daily = self._forecast.daily()

        weather['summary'] = current['summary']
        weather['icon'] = self.get_icon_code(current['icon'])
        weather['temperature'] = int(round(current['temperature']))
        weather['wind_speed'] = int(round(current['windSpeed']))
        weather['wind_bearing'] = self.get_direction(round(current['windBearing']))
        weather['minute_summary'] = self._forecast.minutely().summary
        weather['hour_summary'] = self._forecast.hourly().summary
        weather['sunrise_time'] = daily.data[0].sunriseTime
        weather['sunset_time'] = daily.data[0].sunsetTime
        weather['rises'] = 'Rises' if weather['sunrise_time'] > datetime.now() else 'Rose'
        weather['sets'] = 'Sets' if weather['sunset_time'] > datetime.now() else 'Set'
        weather['url'] = 'http://forecast.io/#/f/{},{}'.format(self._latitude, self._longitude)

        return weather

    def update(self):
        """Updates the forecast information"""
        self._forecast.update()


class PfSense:
    """
    Contains the functionality needed to communicate with a pfSense firewall
    """

    def __init__(self, hostname, username, password, interfaces, **kwargs):
        """Initializes the pfSense firewall communication"""
        self._hostname = hostname
        self._username = username
        self._password = password
        self._interfaces = interfaces
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(self._hostname, username=self._username, password=self._password)
        self.get_current_bandwidth_stats()

    def get_current_bandwidth_usage_on_interface(self, interface_name):
        """
        Connects to pfSense and fetches the current amount of traffic passing
        through the specified interface_name
        """
        stdin, stdout, stderr = self._client.exec_command('vnstat -i {} -tr'.format(interface_name))
        output = stdout.readlines()
        dl_speed_line = str(output[-3])
        ul_speed_line = str(output[-2])

        pattern = re.compile(r'\b[r,t]x\ *(?P<speed>\d*.\d*) (?P<units>[a-zA-z]*/s)')

        match = re.search(pattern, dl_speed_line)
        dl_speed = float(match.group('speed'))
        if match.group('units') == 'kbit/s':
            dl_speed /= 1024
        dl_speed = round(dl_speed, 2)

        match = re.search(pattern, ul_speed_line)
        ul_speed = float(match.group('speed'))
        if match.group('units') == 'kbit/s':
            ul_speed /= 1024
        ul_speed = round(ul_speed, 2)

        return (round(dl_speed, 2), round(ul_speed, 2))

    def get_current_bandwidth_stats(self):
        """
        Loops through all interfaces and gets the amount of traffic passing
        through each of them
        """
        for interface in self._interfaces:
            interface['dl_speed'], interface['ul_speed'] = self.get_current_bandwidth_usage_on_interface(interface['name'])
            interface['dl_usage'] = 100 * interface['dl_speed'] / interface['max_dl_speed']
            interface['ul_usage'] = 100 * interface['ul_speed'] / interface['max_ul_speed']
            interface['ping'] = self.get_current_ping_time_on_interface(interface)

    def get_current_ping_time_on_interface(self, interface):
        """
        Connects to pfSense and gets the average ping time to the specified
        ip address
        """
        stdin, stdout, stderr = self._client.exec_command('ping -S {} -t 5 {}'.format(
            interface['ip'], interface['ping_ip']))
        output = stdout.readlines()
        avg_ping_line = str(output[-1])

        pattern = re.compile(r'\d+.\d*\/(?P<average>\d+.\d*)')

        match = re.search(pattern, avg_ping_line)
        avg_ping = int(round(float(match.group('average')), 0))
        return avg_ping

    def get_interfaces(self):
        """
        Returns a list containing all of the interfaces that we are monitoring
        with the bandwidth usage and ping information appended
        """
        return self._interfaces


@app.before_first_request
def spawn_greenlet():
    """Spawns greenlets to update information from modules via SocketIO"""

    @copy_current_request_context
    def greenlet_get_now_playing():
        """
        A greenlet that communicates with Plex every second to update
        the now playing information via SocketIO
        """

        last_now_playing = True
        while True:
            cur = now_playing()
            if not cur:
                if last_now_playing:
                    socketio.emit('plex', {'data': recently_released()})
                    last_now_playing = False
            else:
                last_now_playing = True
                socketio.emit('plex', {'data': cur})
            gevent.sleep(1)

    gevent.spawn(greenlet_get_now_playing)

    @copy_current_request_context
    def greenlet_get_forecast():
        """
        A greenlet that communicates with Forecast.io every 2 minutes to
        update the weather information via SocketIO
        """

        while True:
            socketio.emit('forecast', {'data': forecast()})
            gevent.sleep(120)
            modules['forecast'].update()

    gevent.spawn(greenlet_get_forecast)

@socketio.on('connect')
def client_connect():
    """
    Send the current information via SocketIO to new clients as
    they connect to the server
    """
    emit('plex', {'data': recently_released() if not now_playing() else now_playing()})
    emit('forecast', {'data': forecast()})
