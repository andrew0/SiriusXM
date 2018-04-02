import requests
import base64
import urllib.parse
import json
import time, datetime
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

class SiriusXM:
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6'
    REST_FORMAT = 'https://player.siriusxm.com/rest/v2/experience/modules/{}'
    LIVE_PRIMARY_HLS = 'https://siriusxm-priprodlive.akamaized.net'

    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.username = username
        self.password = password
        self.playlists = {}
        self.channels = None

    @staticmethod
    def log(x):
        print('{} <SiriusXM>: {}'.format(datetime.datetime.now().strftime('%d.%b %Y %H:%M:%S'), x))

    def is_logged_in(self):
        return 'SXMAUTH' in self.session.cookies

    def is_session_authenticated(self):
        return 'AWSELB' in self.session.cookies and 'JSESSIONID' in self.session.cookies

    def get(self, method, params, authenticate=True):
        if authenticate and not self.is_session_authenticated() and not self.authenticate():
            self.log('Unable to authenticate')
            return None

        res = self.session.get(self.REST_FORMAT.format(method), params=params)
        if res.status_code != 200:
            self.log('Received status code {} for method \'{}\''.format(res.status_code, method))
            return None

        try:
            return res.json()
        except ValueError:
            self.log('Error decoding json for method \'{}\''.format(method))
            return None

    def post(self, method, postdata, authenticate=True):
        if authenticate and not self.is_session_authenticated() and not self.authenticate():
            self.log('Unable to authenticate')
            return None

        res = self.session.post(self.REST_FORMAT.format(method), data=json.dumps(postdata))
        if res.status_code != 200:
            self.log('Received status code {} for method \'{}\''.format(res.status_code, method))
            return None

        try:
            return res.json()
        except ValueError:
            self.log('Error decoding json for method \'{}\''.format(method))
            return None

    def login(self):
        postdata = {
        	'moduleList': {
        		'modules': [{
        			'moduleRequest': {
        				'resultTemplate': 'web',
        				'deviceInfo': {
        					'osVersion': 'Mac',
        					'platform': 'Web',
        					'sxmAppVersion': '3.1802.10011.0',
        					'browser': 'Safari',
        					'browserVersion': '11.0.3',
        					'appRegion': 'US',
        					'deviceModel': 'K2WebClient',
        					'clientDeviceId': 'null',
        					'player': 'html5',
        					'clientDeviceType': 'web',
        				},
        				'standardAuth': {
        					'username': self.username,
        					'password': self.password,
        				},
        			},
        		}],
        	},
        }
        data = self.post('modify/authentication', postdata, authenticate=False)
        if not data:
            return False

        try:
            return data['ModuleListResponse']['status'] == 1 and self.is_logged_in()
        except KeyError:
            self.log('Error decoding json response for login')
            return False

    def authenticate(self):
        if not self.is_logged_in() and not self.login():
            self.log('Unable to authenticate because login failed')
            return False

        postdata = {
        	'moduleList': {
        		'modules': [{
        			'moduleRequest': {
        				'resultTemplate': 'web',
        				'deviceInfo': {
        					'osVersion': 'Mac',
        					'platform': 'Web',
        					'clientDeviceType': 'web',
        					'sxmAppVersion': '3.1802.10011.0',
        					'browser': 'Safari',
        					'browserVersion': '11.0.3',
        					'appRegion': 'US',
        					'deviceModel': 'K2WebClient',
        					'player': 'html5',
        					'clientDeviceId': 'null'
        				}
        			}
        		}]
        	}
        }
        data = self.post('resume?OAtrial=false', postdata, authenticate=False)
        if not data:
            return False

        try:
            return data['ModuleListResponse']['status'] == 1 and self.is_session_authenticated()
        except KeyError:
            self.log('Error parsing json response for authentication')
            return False

    def get_sxmak_token(self):
        try:
            return self.session.cookies['SXMAKTOKEN'].split('=', 1)[1].split(',', 1)[0]
        except (KeyError, IndexError):
            return None

    def get_gup_id(self):
        try:
            return json.loads(urllib.parse.unquote(self.session.cookies['SXMDATA']))['gupId']
        except (KeyError, ValueError):
            return None

    def get_playlist_url(self, guid, channel_id, use_cache=True, max_attempts=5):
        if use_cache and channel_id in self.playlists:
             return self.playlists[channel_id]

        params = {
            'assetGUID': guid,
            'ccRequestType': 'AUDIO_VIDEO',
            'channelId': channel_id,
            'hls_output_mode': 'custom',
            'marker_mode': 'all_separate_cue_points',
            'result-template': 'web',
            'time': int(round(time.time() * 1000.0)),
            'timestamp': datetime.datetime.utcnow().isoformat('T') + 'Z'
        }
        data = self.get('tune/now-playing-live', params)
        if not data:
            return None

        # get status
        try:
            status = data['ModuleListResponse']['status']
            message = data['ModuleListResponse']['messages'][0]['message']
            message_code = data['ModuleListResponse']['messages'][0]['code']
        except (KeyError, IndexError):
            self.log('Error parsing json response for playlist')
            return None

        # login if session expired
        if message_code == 201 or message_code == 208:
            if max_attempts > 0:
                self.log('Session expired, logging in and authenticating')
                if self.authenticate():
                    self.log('Successfully authenticated')
                    return self.get_playlist_url(guid, channel_id, use_cache, max_attempts - 1)
                else:
                    self.log('Failed to authenticate')
                    return None
            else:
                self.log('Reached max attempts for playlist')
                return None
        elif status == 0:
            self.log('Received error {} {}'.format(message_code, message))
            return None

        # get m3u8 url
        try:
            playlists = data['ModuleListResponse']['moduleList']['modules'][0]['moduleResponse']['liveChannelData']['hlsAudioInfos']
        except (KeyError, IndexError):
            self.log('Error parsing json response for playlist')
            return None
        for playlist_info in playlists:
            if playlist_info['size'] == 'LARGE':
                playlist_url = playlist_info['url'].replace('%Live_Primary_HLS%', self.LIVE_PRIMARY_HLS)
                self.playlists[channel_id] = self.get_playlist_variant_url(playlist_url)
                return self.playlists[channel_id]

        return None

    def get_playlist_variant_url(self, url):
        params = {
            'token': self.get_sxmak_token(),
            'consumer': 'k2',
            'gupId': self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code != 200:
            self.log('Received status code {} on playlist variant retrieval'.format(res.status_code))
            return None

        variant = next(filter(lambda x: x.endswith('.m3u8'), map(lambda x: x.rstrip(), res.text.split('\n'))), None)
        return '{}/{}'.format(url.rsplit('/', 1)[0], variant) if variant else None

    def get_playlist(self, name, use_cache=True):
        guid, channel_id = self.get_channel(name)
        if not guid or not channel_id:
            self.log('No channel for {}'.format(name))
            return None

        url = self.get_playlist_url(guid, channel_id, use_cache)
        params = {
            'token': self.get_sxmak_token(),
            'consumer': 'k2',
            'gupId': self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            self.log('Received status code 403 on playlist, renewing session')
            return self.get_playlist(name, False)

        if res.status_code != 200:
            self.log('Received status code {} on playlist variant'.format(res.status_code))
            return None

        # add base path to segments
        lines = list(map(lambda x: x.rstrip(), res.text.split('\n')))
        for x in range(len(lines)):
            line = lines[x].rstrip()
            if line.endswith('.aac'):
                base_url = url.rsplit('/', 1)[0]
                base_path = base_url[8:].split('/', 1)[1]
                lines[x] = '{}/{}'.format(base_path, line)
        return '\n'.join(lines)

    def get_segment(self, path, max_attempts=5):
        print(path)
        url = '{}/{}'.format(self.LIVE_PRIMARY_HLS, path)
        params = {
            'token': self.get_sxmak_token(),
            'consumer': 'k2',
            'gupId': self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            if max_attempts > 0:
                self.log('Received status code 403 on segment, renewing session')
                self.get_playlist(path.split('/', 2)[1], False)
                return self.get_segment(path, max_attempts - 1)
            else:
                self.log('Received status code 403 on segment, max attempts exceeded')
                return None

        if res.status_code != 200:
            self.log('Received status code {} on segment'.format(res.status_code))
            return None

        return res.content

    def get_channel(self, name):
        # download channel list if necessary
        if not self.channels:
            postdata = {
            	'moduleList': {
            		'modules': [{
            			'moduleArea': 'Discovery',
            			'moduleType': 'ChannelListing',
            			'moduleRequest': {
            				'consumeRequests': [],
            				'resultTemplate': 'responsive',
            				'alerts': [],
            				'profileInfos': []
            			}
            		}]
            	}
            }
            data = self.post('get', postdata)
            if not data:
                self.log('Unable to get channel list')
                return (None, None)

            try:
                self.channels = data['ModuleListResponse']['moduleList']['modules'][0]['moduleResponse']['contentData']['channelListing']['channels']
            except (KeyError, IndexError):
                self.log('Error parsing json response for channels')
                return (None, None)

        name = name.lower()
        channel = next(filter(lambda x: x['name'].lower() == name or x['channelId'] == name, self.channels), None)
        return (channel['channelGuid'], channel['channelId']) if channel else (None, None)

def make_sirius_handler(username, password):
    class SiriusHandler(BaseHTTPRequestHandler):
        HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')
        sxm = SiriusXM(username, password)

        def do_GET(self):
            if self.path.endswith('.m3u8'):
                data = self.sxm.get_playlist(self.path.rsplit('/', 1)[1][:-5])
                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/x-mpegURL')
                    self.end_headers()
                    self.wfile.write(bytes(data, 'utf-8'))
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('.aac'):
                data = self.sxm.get_segment(self.path[1:])
                if data:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/x-aac')
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('/key/1'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(self.HLS_AES_KEY)
            else:
                self.send_response(500)
                self.end_headers()
    return SiriusHandler

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('usage: python sxm.py [username] [password] [port]')
        sys.exit(1)

    httpd = HTTPServer(('', int(sys.argv[3])), make_sirius_handler(sys.argv[1], sys.argv[2]))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
