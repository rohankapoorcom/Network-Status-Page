"""
Contains functions and classes needed for processing the Network Status Page
"""

from xml.etree import ElementTree
from flask import copy_current_request_context
from flask_socketio import emit

from status import app, socketio
from status.views import now_playing

import requests
import gevent

class Plex:
    """Contains the functionality needed to communicate with a Plex server"""
    _STATUS_URL = '/status/sessions'

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
        device = unprocessed_video.find('Player').get('title')
        video['user'] = unprocessed_video.find('User').get('title')

        video_tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, metadata_url)
                ).content
            )

        metadata = video_tree.find('Video')
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
        response = requests.get('{}{}'.format(self._server, Plex._STATUS_URL))
        tree = ElementTree.fromstring(response.content)
        tree = ElementTree.fromstring(
            requests.get(
                '{}{}'.format(self._server, Plex._STATUS_URL)
            ).content
        )

        videos = tree.findall('Video')
        if not videos:
            return []
        return [self.process_currently_playing_video(video) for video in videos]
 
    def get_token(self):
        """Returns the authentication token"""
        return self._token

@app.before_first_request
def spawn_greenlet():
    """
    Spawns a greenlet to communicate with Plex every second to update
    the now playing information via SocketIO
    """
    @copy_current_request_context
    def greenlet_get_now_playing():
        while True:
            socketio.emit('status', {'plex': now_playing()})
            gevent.sleep(1)

    gevent.spawn(greenlet_get_now_playing)

@socketio.on('connect')
def client_connect():
    """
    Send the now playing information via SocketIO to new clients as
    they connect to the server
    """
    emit('status', {'plex': now_playing()})
