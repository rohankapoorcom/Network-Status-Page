from xml.etree import ElementTree
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

    def process_currently_playing_video(self, unprocessed_video):
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
        response = requests.get('{}{}'.format(self._server, Plex._STATUS_URL))
        tree = ElementTree.fromstring(response.content)
        videos = tree.findall('Video')
        if not videos:
            return []
        return [self.process_currently_playing_video(video) for video in videos]
 
    def get_token(self):
        return self._token

