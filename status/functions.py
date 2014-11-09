"""
Contains functions and classes needed for processing the Network Status Page
"""

from xml.etree import ElementTree
from flask import copy_current_request_context
from flask_socketio import emit
from datetime import datetime

from status import app, socketio
from status.views import now_playing, recently_released, forecast

import requests
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

        self._token = tree.get('authenticationToken')

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
                '{}{}'.format(self._server, metadata_url)
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
            video['artwork'] = '{}{}'.format(
                self._server,
                metadata.get('thumb')
                )

            video['title'] = metadata.get('title')
            summary = metadata.get('summary')
            video['summary'] = (summary[:800] + '...') if len(summary) > 800 else summary

        elif (video_type == 'episode'):
            video['artwork'] = '{}{}'.format(
                self._server,
                metadata.get('thumb') if not metadata.get('grandparentThumb') else metadata.get('grandparentThumb')
                )

            video['title'] = metadata.get('grandparentTitle')
            video['episode_title'] = metadata.get('title')
            video['summary'] = metadata.get('summary')
            video['season'] = metadata.get('parentIndex')
            video['episode_number'] = metadata.get('index')

        return video

    def get_currently_playing_videos(self):
        """
        Returns a list of dictionaries containing information about all
        currently playing videos
        """
        tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, Plex._STATUS_URL)
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
                '{}{}'.format(self._server, Plex._LIBRARY_URL)
            ).content
        )

        directories = section_tree.findall('Directory')
        return ['{}{}'.format(
            self._server,
            Plex._RELEASED_URL.format(
                directory.find('Location').get('id')
            )
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
                requests.get(section).content
            )

            videos = video_tree.findall('Video')
            processed_videos.extend(self.process_currently_playing_video(video) for video in videos)

        return processed_videos
 
    def get_token(self):
        """Returns the authentication token"""
        return self._token

class ForecastIO:
    """
    A Wrapper for the python-forecastio package allowing one time loading
    of the API key and latitude/longitude coordinates
    """

    #### Update Forecast every 1.5 minutes

    def __init__(self, api_key, latitude, longitude, **kwargs):
        """Initializes an instance of the ForecastIO wrapper"""
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.forecast = forecastio.load_forecast(self.api_key, self.latitude, self.longitude)

    def get_direction(self, bearing):
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
        return directions[int(round(bearing/45))]

    def get_icon_code(self, icon):
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
        current = self.forecast.currently().d
        daily = self.forecast.daily()

        weather['summary'] = current['summary']
        weather['icon'] = self.get_icon_code(current['icon'])
        weather['temperature'] = int(round(current['temperature']))
        weather['wind_speed'] = int(round(current['windSpeed']))
        weather['wind_bearing'] = self.get_direction(round(current['windBearing']))
        weather['minute_summary'] = self.forecast.minutely().summary
        weather['hour_summary'] = self.forecast.hourly().summary
        weather['sunrise_time'] = daily.data[0].sunriseTime
        weather['sunset_time'] = daily.data[0].sunsetTime
        weather['rises'] = 'Rises' if weather['sunrise_time'] > datetime.now() else 'Rose'
        weather['sets'] = 'Sets' if weather['sunset_time'] > datetime.now() else 'Set'
        weather['url'] = 'http://forecast.io/#/f/{},{}'.format(self.latitude, self.longitude)

        return weather

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
                    socketio.emit('plex', {'data': recently_released() })
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
            socketio.emit('forecast', {'data': forecast() })
            gevent.sleep(120)
            
    gevent.spawn(greenlet_get_forecast)

@socketio.on('connect')
def client_connect():
    """
    Send the current information via SocketIO to new clients as
    they connect to the server
    """
    emit('plex', {'data': recently_released() if not now_playing() else now_playing() })
    emit('forecast', {'data': forecast() })
