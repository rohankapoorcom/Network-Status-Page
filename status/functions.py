from xml.etree import ElementTree
import urllib.parse
import requests

class Plex:
    _STATUS_URL = '/status/sessions'

    def __init__(self, username, password, server_name, api_token_uri, **kwargs):
        self._username = username
        self._password = password
        self._server = server_name
        self._token_url = api_token_uri
        self.fetch_token()

    def fetch_token(self):
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

    def get_currently_playing_videos(self):
        now_playing_videos = []
        response = requests.get('{}{}'.format(self._server, Plex._STATUS_URL))
        tree = ElementTree.fromstring(response.content)
        videos = tree.findall('Video')
        if not videos:
            return []

        for video in videos:
            now_playing_video = {}
            metadata_url = video.get('key')
            device = video.find('Player').get('title')
            now_playing_video['user'] = video.find('User').get('title')

            video_tree = ElementTree.fromstring(
                requests.get(
                    '{}{}'.format(self._server, metadata_url)
                    ).content
                )

            metadata = video_tree.find('Video')
            video_type = metadata.get('type')
            now_playing_video['type'] = video_type

            if (video_type == 'movie'):
                now_playing_video['artwork'] = '{}{}'.format(
                    self._server,
                    urllib.parse.quote(metadata.get('thumb'))
                    )

                now_playing_video['title'] = metadata.get('title')
                summary = metadata.get('summary')
                now_playing_video['summary'] = (summary[:800] + '...') if len(summary) > 800 else summary

            elif (video_type == 'episode'):
                now_playing_video['artwork'] = '{}{}'.format(
                    self._server,
                    urllib.parse.quote(metadata.get('grandparentThumb'))
                    )

                now_playing_video['title'] = metadata.get('grandparentTitle')
                now_playing_video['episode_title'] = metadata.get('grandparentTitle')
                now_playing_video['summary'] = metadata.get('summary')
                now_playing_video['season'] = metadata.get('parentIndex')
                now_playing_video['episode_number'] = metadata.get('index')

            now_playing_videos.append(now_playing_video)

        return now_playing_videos
 
    def get_token(self):
        return self._token

