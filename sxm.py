import re
import requests
import base64
import urllib.parse
import json
import time
import sys
import subprocess
import datetime
import traceback
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed
from tenacity import retry_if_result

from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from concurrent.futures import ThreadPoolExecutor


class AuthenticationError(Exception):
    pass


class SegmentRetrievalException(Exception):
    pass


def retry_login(value):
    if value is False:
        print("Retrying login..")
        sys.stdout.flush()

    return value is False


def retry_authenticate(value):
    if value is False:
        print("Retrying authenticate..")
        sys.stdout.flush()

    return value is False

class SiriusXM:
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6'
    REST_FORMAT = 'https://player.siriusxm.com/rest/v2/experience/modules/{}'
    LIVE_PRIMARY_HLS = 'https://siriusxm-priprodlive.akamaized.net'

    LAYERS = {
        'cut': 0,
        'segment': 1,
        'episode': 2,
        'future-episode': 3,
        'companioncontent': 4
    }

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

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(10))
    def get(self, method, params):
        if self.is_session_authenticated() and not self.authenticate():
            self.log('Unable to authenticate')
            return None

        try:
            res = self.session.get(self.REST_FORMAT.format(method), params=params)
        except requests.exceptions.ConnectionError as e:
            self.log("An Exception occurred when trying to perform the GET request!")
            self.log("\tParams: {}".format(params))
            self.log("\tMethod: {}".format(method))
            self.log("Response: {}".format(e.response))
            self.log("Request: {}".format(e.request))
            raise(e)

        if res.status_code != 200:
            self.log('Received status code {} for method \'{}\''.format(res.status_code, method))
            return None

        try:
            return res.json()
        except ValueError:
            self.log('Error decoding json for method \'{}\''.format(method))
            return None

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(10))
    def post(self, method, postdata, authenticate=True):
        if authenticate and not self.is_session_authenticated() and not self.authenticate():
            self.log('Unable to authenticate')
            return None

        res = None

        try:
            res = self.session.post(self.REST_FORMAT.format(method), data=json.dumps(postdata))
        except requests.exceptions.ConnectionError as e:
            self.log("Connection error on POST")
            raise(e)

        if res is not None and res.status_code != 200:
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

        try:
            return data['ModuleListResponse']['status'] == 1 and self.is_logged_in()
        except KeyError:
            self.log('Error decoding json response for login')
            import pdb; pdb.set_trace()
            return False

    def authenticate(self):
        if not self.is_logged_in() and not self.login():
            self.log("Unable to authenticate because login failed")
            return False
            # raise AuthenticationError("Unable to authenticate because login failed")

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

    def get_episodes(self, channel_name):
        channel_guid, channel_id = self.get_channel(channel_name)

        now_playing = self.get_now_playing(channel_guid, channel_id)
        episodes = []

        if now_playing is None:
            pass


        for marker in now_playing['ModuleListResponse']['moduleList']['modules'][0]['moduleResponse']['liveChannelData']['markerLists'][self.LAYERS['episode']]['markers']:
            start = datetime.datetime.strptime(marker['timestamp']['absolute'], '%Y-%m-%dT%H:%M:%S.%f%z')
            end = start + timedelta(seconds=marker['duration'])

            start = start.replace(tzinfo=None)
            end = end.replace(tzinfo=None)

            episodes.append({
                    'mediumTitle': marker['episode'].get('mediumTitle', 'UnknownMediumTitle'),
                    'longTitle': marker['episode'].get('longTitle', 'UnknownLongTitle'),
                    'shortDescription': marker['episode'].get('shortDescription', 'UnknownShortDescription'),
                    'longDescription': marker['episode'].get('longDescription', 'UnknownLongDescription'),
                    'start': start,
                    'end': end
                })

        return episodes

    def get_current_episode(self):
        for episode in self.get_episodes('shade45'):
            now = datetime.datetime.utcnow()

            if not all(['start' in episode, 'end' in episode]):
                self.log("Missing start/end keys in episode: {}".format(episode))
                continue

            if episode['start'] < now < episode['end']:
                return episode

    def get_now_playing(self, guid, channel_id):
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

        return self.get('tune/now-playing-live', params)

    def get_playlist_url(self, guid, channel_id, use_cache=True, max_attempts=5):
        if use_cache and channel_id in self.playlists:
             return self.playlists[channel_id]

        data = self.get_now_playing(guid, channel_id)

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

    @retry(stop=stop_after_attempt(25), wait=wait_fixed(1))
    def get_playlist(self, name, use_cache=True):
        guid, channel_id = self.get_channel(name)

        if not all([guid, channel_id]):
            self.log('No channel for {}'.format(name))
            return None

        res = None
        url = self.get_playlist_url(guid, channel_id, use_cache)

        try:
            params = {'token': self.get_sxmak_token(), 'consumer': 'k2', 'gupId': self.get_gup_id()}
            res = self.session.get(url, params=params)

            if res.status_code == 403:
                self.log('Received status code 403 on playlist, renewing session')
                return self.get_playlist(name, False)

            if res.status_code != 200:
                self.log('Received status code {} on playlist variant'.format(res.status_code))
                return None

        except requests.exceptions.ConnectionError as e:
            self.log("Error getting playlist: {}".format(e))

        playlist_entries = []
        for line in res.text.split('\n'):
            line = line.strip()
            playlist_entries.append(re.sub("[^\/]\w+\.m3u8", line, re.findall("AAC_Data.*", url)[0]))

        return '\n'.join(playlist_entries)

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def get_segment(self, path):
        url = '{}/{}'.format(self.LIVE_PRIMARY_HLS, path)
        params = {
            'token': self.get_sxmak_token(),
            'consumer': 'k2',
            'gupId': self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            self.get_playlist(path.split('/', 2)[1], False)
            raise SegmentRetrievalException("Received status code 403 on segment, renewed session")

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

        # TODO: Refactor
        name = name.lower()
        for x in self.channels:
            if x.get('name', '').lower() == name or x.get('channelId', '').lower() == name or x.get('siriusChannelNumber') == name:
                return (x['channelGuid'], x['channelId'])
        return (None, None)

def make_sirius_handler(username, password):
    class SiriusHandler(BaseHTTPRequestHandler):
        HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')
        sxm = SiriusXM(username, password)

        def do_GET(self):
            if self.path.endswith('.m3u8'):
                data = self.sxm.get_playlist(self.path.rsplit('/', 1)[1][:-5])
                if data:
                    try:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/x-mpegURL')
                        self.end_headers()
                        self.wfile.write(bytes(data, 'utf-8'))
                    except Exception as e:
                        self.sxm.log("Error sending playlist to client!")
                        traceback.print_exc()
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('.aac'):
                data = self.sxm.get_segment(self.path[1:])
                if data:
                    try:
                        self.send_response(200)
                        self.send_header('Content-Type', 'audio/x-aac')
                        self.end_headers()
                        self.wfile.write(data)
                    except BrokenPipeError as e:
                        self.sxm.log("Error sending stream data to the client; connection terminated?")
                        traceback.print_exc()

                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith('/key/1'):
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(self.HLS_AES_KEY)
                except Exception as e:
                    self.sxm.log("Error sending HLS_AES_KEY to client")
                    traceback.print_exc()
            else:
                self.send_response(500)
                self.end_headers()
    return SiriusHandler


def start_httpd(handler):
    httpd = HTTPServer(('', int(sys.argv[3])), handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


class SiriusXMRipper(object):
    def __init__(self, handler):
        self.handler = handler
        self.episode = None
        self.last_episode = None
        self.pid = None
        self.proc = None
        self.completed_files = []
        self.recorded_shows = json.load(open('config.json', 'r'))['shows']
        self.start = time.time()

    def should_record_current_episode(self):
        shows = re.compile('|'.join(self.recorded_shows), re.IGNORECASE)

        if self.episode is None:
            self.handler.sxm.log("Current episode is None; cannot check if current episode should be recorded")
            return False

        for k, v in self.episode.items():
            try:
                if shows.findall(v):
                    return True
            except TypeError:
                continue

        return False

    def wait_for_episode_title(self):
        episode = self.handler.sxm.get_current_episode()

        while episode is None or episode.get('longTitle') == 'UnknownLongTitle':
            self.handler.sxm.log("Current episode registered incorrectly; fetching again..")
            time.sleep(30)

        self.episode = episode

    def poll_episodes(self):
        while True:
            try:
                self.wait_for_episode_title()

                if self.last_episode != self.episode:
                    self.last_episode = self.episode

                    self.handler.sxm.log(
                        "\033[0;32mCurrent Episode:\033[0m {} - {}"
                        "(\033[0;32m{}\033[0m remaining)".format(
                            self.episode['longTitle'], self.episode['longDescription'],
                            self.episode['end'] - datetime.datetime.utcnow()))

                    if self.proc is not None:
                        self.proc.terminate()
                        self.proc = None

            except Exception as e:
                self.handler.sxm.log("Exception occurred in Ripper.poll_episodes: {}".format(e))
                traceback.print_exc()

            if self.should_record_current_episode():
                if self.proc is None or self.proc is not None and self.proc.poll() is not None:
                    self.rip_stream()

            time.sleep(60)

    def rip_stream(self):
        try:
            filename = time.strftime("%Y-%m-%d_%H_%M_%S_{}.mp3".format('_'.join(self.episode['mediumTitle'].split())))
            cmd = "/usr/local/bin/ffmpeg -i http://127.0.0.1:8888/shade45.m3u8 -acodec libmp3lame -ac 2 -ab 160k {}".format(filename)
            self.handler.sxm.log("Executing: {}".format(cmd))
            self.proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=False)
        except Exception as e:
            self.handler.sxm.log("Exception occurred in Ripper.rip_stream: {}".format(e))


if __name__ == '__main__':
    sirius_handler = make_sirius_handler(sys.argv[1], sys.argv[2])
    ripper = SiriusXMRipper(sirius_handler)

    executor = ThreadPoolExecutor(max_workers=2)

    if len(sys.argv) < 4:
        print('usage: python sxm.py [username] [password] [port]')
        sys.exit(1)

    httpd_thread = executor.submit(start_httpd, sirius_handler)
    episode_thread = executor.submit(ripper.poll_episodes)

    while True:
        for index, thread in enumerate([httpd_thread, episode_thread]):
            if thread.done():
                sirius_handler.sxm.log("Thread{} exited/terminated -- result:{}".format(index, thread.result()))

        time.sleep(60)
