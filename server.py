#!/usr/bin/env python
#
# Copyright (c) 2015 andrew0
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
#
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
#
# 3. This notice may not be removed or altered from any source distribution.
#

import sys
import time
import BaseHTTPServer
import requests
import base64
import json
import datetime
from channels import *

SIRIUS_USERNAME = ''
SIRIUS_PASSWORD = ''

class SiriusXM:
    BASE_URL = 'https://player.siriusxm.com/rest/v1/experience/modules'
    HLS_BASE_URL = 'http://primary.hls-streaming.production.streaming.siriusxm.com/AAC_Data'
    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'

    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.username = username
        self.password = password
        # self.login()

    def login(self):
        url = '%s/modify/authentication' % (self.BASE_URL)
        postdata = {
            'moduleList': {
                'modules': [{
                    'moduleRequest': {
                        'resultTemplate': 'web',
                        'deviceInfo': {
                            'osVersion': 'Mac',
                            'platform': 'Web',
                            'sxmAppVersion': 'v.0316',
                            'browser': 'Chrome',
                            'browserVersion': '41.0.2272.101',
                            'deviceModel': 'K2WebClient',
                            'appRegion': 'US',
                            'clientDeviceId': 'null',
                        },
                        'standardAuth': {
                            'username': self.username,
                            'password': self.password,
                        },
                    },
                }],
            },
        }
        res = self.session.post(url, data=json.dumps(postdata))

        if res.status_code != 200:
            print '%s: Received status code %d ' % (sys._getframe().f_code.co_name, res.status_code)
            return False

        try:
            return res.json()['ModuleListResponse']['status'] == 1
        except:
            return False

    def get_auth_token(self, channel_number):
        channel_id = get_channel_id(channel_number)
        if channel_id is None:
            return False

        ts = int(round(time.time() * 1000))
        rfc3339 = datetime.datetime.utcnow().isoformat('T') + 'Z'
        url = '%s/tune/now-playing-live?ccRequestType=AUDIO_VIDEO&hls_output_mode=custom&id=%s&marker_mode=all_separate_cue_points&result-template=web&time=%d&timestamp=%s' % (self.BASE_URL, channel_id, ts, rfc3339)
        res = self.session.get(url)

        if res.status_code != 200:
            print '%s: Received status code %d ' % (sys._getframe().f_code.co_name, res.status_code)
            return False

        # login if session expired
        try:
            if res.json()['ModuleListResponse']['status'] == 0:
                print 'Session expired, logging in'
                if self.login():
                    print 'Successfully logged in'
                    return self.get_auth_token(channel_number)
                else:
                    print 'Unable to login'
                    return False
        except:
            return False

        return 'SXMAKTOKEN' in res.cookies

    def get_playlist(self, channel_number):
        channel_id = get_channel_id(channel_number)
        if channel_id is None:
            return False

        url = '%s/%s/HLS_%s_256k_v3/%s_256k_large_v3.m3u8' % (self.HLS_BASE_URL, channel_id, channel_id, channel_id)
        res = self.session.get(url)
        if res.status_code == 200:
            return res
        elif res.status_code == 403:
            print 'Received 403 Forbidden, renewing token'
            if self.get_auth_token(channel_number):
                return self.get_playlist(channel_number)
            else:
                return None
        elif res.status_code == 503:
            time.sleep(3)
            return self.get_playlist(channel_number)
        else:
            return None

    def get_segment(self, name):
        channel_id = name.split('_', 1)[0]
        url = '%s/%s/HLS_%s_256k_v3/%s' % (self.HLS_BASE_URL, channel_id, channel_id, name)
        res = self.session.get(url, stream=True)
        if res.status_code == 200:
            return res
        elif res.status_code == 403:
            print 'Received 403 Forbidden, renewing token'
            if self.get_auth_token(get_channel_number(channel_id)):
                return self.get_segment(name)
            else:
                return None
        elif res.status_code == 503:
            time.sleep(3)
            return self.get_segment(name)
        else:
            return None

class SiriusHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    HLS_AES_KEY = base64.b64decode('0Nsco7MAgxowGvkUT8aYag==')
    sxm = SiriusXM(SIRIUS_USERNAME, SIRIUS_PASSWORD)

    def handle_key(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(self.HLS_AES_KEY)

    def handle_playlist(self):
        channel_number = self.path.split('/')[-1][:-5]
        res = self.sxm.get_playlist(channel_number)

        if res is not None and res.status_code == 404:
            print 'Channel %d not found' % (channel_number)
            self.send_response(404)
            self.end_headers()
            return True
        elif res is not None and res.status_code == 200:
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-mpegURL')
            self.end_headers()
            self.wfile.write(res.text)
            return True

        return False

    def handle_segment(self):
        res = None
        data = None

        for attempts in range(3):
            try:
                res = self.sxm.get_segment(self.path[1:])
                data = res.raw.read() if res is not None and res.status_code == 200 else None
                break
            except:
                # try one more time
                print 'Received IncompleteRead exception, trying again'

        if res is None or data is None:
            return False

        if res.status_code == 404:
            print 'Segment %s not found' % (self.path[1:])
            self.send_response(404)
            self.end_headers()
            return True
        elif res.status_code == 200:
            self.send_response(200)
            self.send_header('Content-Type', 'audio/x-aac')
            self.end_headers()
            self.wfile.write(data)
            return True

        return False

    def do_GET(self):
        '''Respond to a GET request.'''
        try:
            if self.path.find('/key/') != -1:
                self.handle_key()
                return
            elif self.path.endswith('.m3u8'):
                if self.handle_playlist():
                    return
            elif self.path.endswith('.aac'):
                if self.handle_segment():
                    return
            else:
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(500)
            self.end_headers()
        except:
            print 'Received broken pipe, ignoring...'

if __name__ == '__main__':
    httpd = BaseHTTPServer.HTTPServer(('', 9001), SiriusHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
