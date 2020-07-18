import argparse
import eyed3
import os
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
from collections import defaultdict
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

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
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6"
    REST_FORMAT = "https://player.siriusxm.com/rest/v2/experience/modules/{}"
    LIVE_PRIMARY_HLS = "https://siriusxm-priprodlive.akamaized.net"

    def __init__(self, username, password, output_directory=os.path.abspath(".")):
        self.username = username
        self.password = password
        self.reset_session()
        self.playlists = {}
        self.channels = None
        self.output_directory = output_directory

    @staticmethod
    def log(x):
        print(
            "{} <SiriusXM>: {}".format(
                datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"), x
            )
        )

    def is_logged_in(self):
        return "SXMAUTHNEW" in self.session.cookies

    def is_session_authenticated(self):
        return "AWSELB" in self.session.cookies and "JSESSIONID" in self.session.cookies

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(10))
    def get(self, method, params):
        if self.is_session_authenticated() and not self.authenticate():
            self.log("Unable to authenticate")
            return None

        try:
            res = self.session.get(self.REST_FORMAT.format(method), params=params)
        except requests.exceptions.ConnectionError as e:
            self.log("An Exception occurred when trying to perform the GET request!")
            self.log("\tParams: {}".format(params))
            self.log("\tMethod: {}".format(method))
            self.log("Response: {}".format(e.response))
            self.log("Request: {}".format(e.request))
            raise (e)

        if res.status_code != 200:
            self.log(
                "Received status code {} for method '{}'".format(
                    res.status_code, method
                )
            )
            return None

        try:
            return res.json()
        except ValueError:
            self.log("Error decoding json for method '{}'".format(method))
            return None

    def post(self, method, postdata, authenticate=True):
        if (
            authenticate
            and not self.is_session_authenticated()
            and not self.authenticate()
        ):
            self.log("Unable to authenticate")
            return None

        res = self.session.post(
            self.REST_FORMAT.format(method), data=json.dumps(postdata)
        )
        if res.status_code != 200:
            self.log(
                "Received status code {} for method '{}'".format(
                    res.status_code, method
                )
            )
            return None

        try:
            return res.json()
        except ValueError:
            self.log("Error decoding json for method '{}'".format(method))
            return None

    def login(self):
        postdata = {
            "moduleList": {
                "modules": [
                    {
                        "moduleRequest": {
                            "resultTemplate": "web",
                            "deviceInfo": {
                                "osVersion": "Mac",
                                "platform": "Web",
                                "sxmAppVersion": "3.1802.10011.0",
                                "browser": "Safari",
                                "browserVersion": "11.0.3",
                                "appRegion": "US",
                                "deviceModel": "K2WebClient",
                                "clientDeviceId": "null",
                                "player": "html5",
                                "clientDeviceType": "web",
                            },
                            "standardAuth": {
                                "username": self.username,
                                "password": self.password,
                            },
                        }
                    }
                ]
            }
        }

        data = self.post("modify/authentication", postdata, authenticate=False)

        try:
            return data["ModuleListResponse"]["status"] == 1 and self.is_logged_in()
        except KeyError:
            self.log("Error decoding json response for login")
            return False

    def reset_session(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(10))
    def authenticate(self):
        if not self.is_logged_in() and not self.login():
            self.log("Authentication failed.. retrying")
            self.reset_session()
            raise AuthenticationError("Reset session")

            # raise AuthenticationError("Unable to authenticate because login failed")

        postdata = {
            "moduleList": {
                "modules": [
                    {
                        "moduleRequest": {
                            "resultTemplate": "web",
                            "deviceInfo": {
                                "osVersion": "Mac",
                                "platform": "Web",
                                "clientDeviceType": "web",
                                "sxmAppVersion": "3.1802.10011.0",
                                "browser": "Safari",
                                "browserVersion": "11.0.3",
                                "appRegion": "US",
                                "deviceModel": "K2WebClient",
                                "player": "html5",
                                "clientDeviceId": "null",
                            },
                        }
                    }
                ]
            }
        }

        # TODO: This raised an exception on DNS lookup
        data = self.post("resume?OAtrial=false", postdata, authenticate=False)
        if not data:
            return False

        try:
            return (
                data["ModuleListResponse"]["status"] == 1
                and self.is_session_authenticated()
            )
        except KeyError:
            self.log("Error parsing json response for authentication")
            return False

    def get_sxmak_token(self):
        try:
            # return "d=1588403836_6524c27821b08a50a19157a06934f59e,v=1,"
            return self.session.cookies["SXMAKTOKEN"].split("=", 1)[1].split(",", 1)[0]
        except (KeyError, IndexError):
            return None

    def get_gup_id(self):
        try:
            return json.loads(urllib.parse.unquote(self.session.cookies["SXMDATA"]))[
                "gupId"
            ]
        except (KeyError, ValueError):
            return None

    def get_episodes(self, channel_name):
        channel_guid, channel_id = self.get_channel(channel_name)

        now_playing = self.get_now_playing(channel_guid, channel_id)
        episodes = []

        if now_playing is None:
            pass

        for marker_list in now_playing["ModuleListResponse"]["moduleList"]["modules"][
            0
        ]["moduleResponse"]["liveChannelData"]["markerLists"]:

            # The location of the episode layer is not always the same!
            if marker_list["layer"] in ["episode", "future-episode"]:

                for marker in marker_list["markers"]:
                    start = datetime.datetime.strptime(
                        marker["timestamp"]["absolute"], "%Y-%m-%dT%H:%M:%S.%f%z"
                    )
                    end = start + timedelta(seconds=marker["duration"])

                    start = start.replace(tzinfo=None)
                    end = end.replace(tzinfo=None)

                    if datetime.datetime.utcnow() > end:
                        continue

                    episodes.append(
                        {
                            "mediumTitle": marker["episode"].get(
                                "mediumTitle", "UnknownMediumTitle"
                            ),
                            "longTitle": marker["episode"].get(
                                "longTitle", "UnknownLongTitle"
                            ),
                            "shortDescription": marker["episode"].get(
                                "shortDescription", "UnknownShortDescription"
                            ),
                            "longDescription": marker["episode"].get(
                                "longDescription", "UnknownLongDescription"
                            ),
                            "start": start,
                            "end": end,
                        }
                    )

        return episodes

    def get_now_playing(self, guid, channel_id):
        params = {
            "assetGUID": guid,
            "ccRequestType": "AUDIO_VIDEO",
            "channelId": channel_id,
            "hls_output_mode": "custom",
            "marker_mode": "all_separate_cue_points",
            "result-template": "web",
            "time": int(round(time.time() * 1000.0)),
            "timestamp": datetime.datetime.utcnow().isoformat("T") + "Z",
        }

        return self.get("tune/now-playing-live", params)

    def get_playlist_url(self, guid, channel_id, use_cache=True, max_attempts=5):
        if use_cache and channel_id in self.playlists:
            return self.playlists[channel_id]

        data = self.get_now_playing(guid, channel_id)

        # get status
        try:
            status = data["ModuleListResponse"]["status"]
            message = data["ModuleListResponse"]["messages"][0]["message"]
            message_code = data["ModuleListResponse"]["messages"][0]["code"]
        except (KeyError, IndexError):
            self.log("Error parsing json response for playlist")
            return None

        # login if session expired
        if message_code == 201 or message_code == 208:
            if max_attempts > 0:
                self.log("Session expired, logging in and authenticating")
                if self.authenticate():
                    self.log("Successfully authenticated")
                    return self.get_playlist_url(
                        guid, channel_id, use_cache, max_attempts - 1
                    )
                else:
                    self.log("Failed to authenticate")
                    return None
            else:
                self.log("Reached max attempts for playlist")
                return None
        elif message_code != 100:
            self.log("Received error {} {}".format(message_code, message))
            return None

        # get m3u8 url
        try:
            playlists = data["ModuleListResponse"]["moduleList"]["modules"][0][
                "moduleResponse"
            ]["liveChannelData"]["hlsAudioInfos"]
        except (KeyError, IndexError):
            self.log("Error parsing json response for playlist")
            return None
        for playlist_info in playlists:
            if playlist_info["size"] == "LARGE":
                playlist_url = playlist_info["url"].replace(
                    "%Live_Primary_HLS%", self.LIVE_PRIMARY_HLS
                )
                self.playlists[channel_id] = self.get_playlist_variant_url(playlist_url)
                return self.playlists[channel_id]

        return None

    def get_playlist_variant_url(self, url):
        params = {
            "token": self.get_sxmak_token(),
            "consumer": "k2",
            "gupId": self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code != 200:
            self.log(
                "Received status code {} on playlist variant retrieval".format(
                    res.status_code
                )
            )
            return None

        variant = next(
            filter(
                lambda x: x.endswith(".m3u8"),
                map(lambda x: x.rstrip(), res.text.split("\n")),
            ),
            None,
        )
        return "{}/{}".format(url.rsplit("/", 1)[0], variant) if variant else None

    @retry(stop=stop_after_attempt(25), wait=wait_fixed(1))
    def get_playlist(self, name, use_cache=True):
        guid, channel_id = self.get_channel(name)

        if not all([guid, channel_id]):
            self.log("No channel for {}".format(name))
            return None

        res = None
        url = self.get_playlist_url(guid, channel_id, use_cache)

        try:
            params = {
                "token": self.get_sxmak_token(),
                "consumer": "k2",
                "gupId": self.get_gup_id(),
            }
            res = self.session.get(url, params=params)

            if res.status_code == 403:
                self.log("Received status code 403 on playlist, renewing session")
                return self.get_playlist(name, False)

            if res.status_code != 200:
                self.log(
                    "Received status code {} on playlist variant".format(
                        res.status_code
                    )
                )
                return None

        except requests.exceptions.ConnectionError as e:
            self.log("Error getting playlist: {}".format(e))

        playlist_entries = []
        for line in res.text.split("\n"):
            line = line.strip()
            if line.endswith(".aac"):
                playlist_entries.append(
                    re.sub("[^\/]\w+\.m3u8", line, re.findall("AAC_Data.*", url)[0])
                )
            else:
                playlist_entries.append(line)

        return "\n".join(playlist_entries)

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5))
    def get_segment(self, path):
        url = "{}/{}".format(self.LIVE_PRIMARY_HLS, path)
        params = {
            "token": self.get_sxmak_token(),
            "consumer": "k2",
            "gupId": self.get_gup_id(),
        }
        res = self.session.get(url, params=params)

        if res.status_code == 403:
            self.get_playlist(path.split("/", 2)[1], False)
            raise SegmentRetrievalException(
                "Received status code 403 on segment, renewed session"
            )

        if res.status_code != 200:
            self.log("Received status code {} on segment".format(res.status_code))
            return None

        return res.content

    def get_channels(self):
        # download channel list if necessary
        if not self.channels:
            postdata = {
                "moduleList": {
                    "modules": [
                        {
                            "moduleArea": "Discovery",
                            "moduleType": "ChannelListing",
                            "moduleRequest": {
                                "consumeRequests": [],
                                "resultTemplate": "responsive",
                                "alerts": [],
                                "profileInfos": [],
                            },
                        }
                    ]
                }
            }

            try:
                if not self.is_session_authenticated():
                    self.authenticate()
            except Exception as e:
                self.log(e)

            channel_list_uri = "get/discover-channel-list?type=2&batch-mode=true&format=json&request-option=discover-channel-list-withpdt&result-template=web"
            data = self.get(channel_list_uri, postdata)
            if not data:
                self.log("Unable to get channel list")
                return None, None

            try:
                self.channels = data["ModuleListResponse"]["moduleList"]["modules"][0][
                    "moduleResponse"
                ]["moduleDetails"]["liveChannelResponse"]["liveChannelResponses"]
            except (KeyError, IndexError):
                self.log("Error parsing json response for channels")
                return []
        return self.channels

    def get_channel(self, name):
        name = name.lower()
        for x in self.get_channels():
            try:
                if (
                    x.get("name", "").lower() == name
                    or x.get("channelId", "").lower() == name
                    or x.get("siriusChannelNumber") == name
                ):
                    return (
                        x["markerLists"][0]["markers"][0]["containerGUID"],
                        x["channelId"],
                    )
            except Exception as e:
                self.log(e)

        return None, None


def make_sirius_handler(args):
    class SiriusHandler(BaseHTTPRequestHandler):
        HLS_AES_KEY = base64.b64decode("0Nsco7MAgxowGvkUT8aYag==")
        sxm = SiriusXM(args.user, args.passwd, args.output_directory)

        def do_GET(self):
            if self.path.endswith(".m3u8"):
                data = self.sxm.get_playlist(self.path.rsplit("/", 1)[1][:-5])
                if data:
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/x-mpegURL")
                        self.end_headers()
                        self.wfile.write(bytes(data, "utf-8"))
                    except Exception as e:
                        self.sxm.log("Error sending playlist to client!")
                        traceback.print_exc()
                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith(".aac"):
                data = self.sxm.get_segment(self.path[1:])
                if data:
                    try:
                        self.send_response(200)
                        self.send_header("Content-Type", "audio/x-aac")
                        self.end_headers()
                        self.wfile.write(data)
                    except BrokenPipeError as e:
                        self.sxm.log("Client stream closed!")

                else:
                    self.send_response(500)
                    self.end_headers()
            elif self.path.endswith("/key/1"):
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
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
    args = parse_args()

    httpd = HTTPServer(("", int(args.port)), handler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


class SiriusXMRipper(object):
    DEFAULT_BITRATE = "160k"

    def __init__(self, handler, args):
        self.handler = handler
        self.episode = None
        self.last_episode = None
        self.pid = None
        self.proc = None
        self.completed_files = []

        try:
            if args.file:
                self.config = json.load(open(args.file, "r"))
            else:
                self.config = json.load(open("config.json"))
        except Exception as e:
            self.handler.sxm.log(f"\033[0;31mWARNING: No config file specified and no default config.json found in relative script path -- entering default mode; bitrate: {self.DEFAULT_BITRATE}\033[0m")
            self.config = {}

        self.bitrate = self.config.get("bitrate", self.DEFAULT_BITRATE)
        self.recorded_shows = self.config.get("shows", [])
        self.tags = self.config.get("tags", {})

        self.track_parts = defaultdict(int)
        self.current_filename = None
        self.output_directory = args.output_directory

        self.handler.sxm.log("\033[0;4;32mRecording the following shows\033[0m")
        for show in self.recorded_shows:
            self.handler.sxm.log("\t{}".format(show))

        self.handler.sxm.log(
            f"\033[0;4;32mDumping music to: {args.output_directory}\033[0m"
        )

        self.handler.sxm.log("\033[0;4;32mAutomatic tagging data\033[0m")
        for show, metadata in self.tags.items():
            self.handler.sxm.log(
                "\tArtist: {} | Album: {} | Genre: {}".format(
                    metadata["artist"], metadata["album"], metadata["genre"]
                )
            )

        self.channel = args.channel
        self.start = time.time()

    def should_record_episode(self, episode):
        shows = re.compile("|".join(self.recorded_shows), re.IGNORECASE)

        for k, v in episode.items():
            try:
                if shows.findall(v):
                    return True
            except TypeError:
                continue

        return False

    def get_current_episode(self, episodes):
        for episode in episodes:
            now = datetime.datetime.utcnow()

            if episode["start"] < now < episode["end"]:
                return episode

        return None

    def display_episodes(self, episodes):
        for episode in sorted(episodes, key=lambda e: e["start"]):
            if episode["start"] < datetime.datetime.utcnow() < episode["end"]:
                self.handler.sxm.log(
                    "\033[0;32mNow Playing:\033[0m {} - {} "
                    "(\033[0;32m{}\033[0m remaining)".format(
                        episode["longTitle"],
                        episode["longDescription"],
                        episode["end"] - datetime.datetime.utcnow(),
                    )
                )
            elif episode["start"] > datetime.datetime.utcnow():
                self.handler.sxm.log(
                    "\033[0;36mComing Up:\033[0m {} - {} "
                    "(\033[0;36m{}\033[0m long)".format(
                        episode["longTitle"],
                        episode["longDescription"],
                        episode["end"] - episode["start"],
                    )
                )

    def get_episode_list(self):
        episodes = None
        episode = None

        while not episodes:
            try:
                episodes = self.handler.sxm.get_episodes(self.channel)
            except KeyError as e:
                self.handler.sxm.log("Episodes list seems borked.. will retry..")

            if episodes is not None:
                episode = self.get_current_episode(episodes)

                if episode is not None:
                    break
                else:
                    time.sleep(15)
                    continue

            else:
                time.sleep(15)
                self.handler.sxm.log("Waiting for episode list..")

        return episodes

    def poll_episodes(self):

        episodes = None
        episode = None

        while True:

            if episodes is None:
                episodes = self.get_episode_list()

            if episode is None or datetime.datetime.utcnow() > episode["end"]:
                self.display_episodes(episodes)

                current_episode = self.get_current_episode(episodes)

                if (
                    not current_episode
                    or current_episode["longTitle"] == "UnknownLongTitle"
                ):
                    episodes = None
                    time.sleep(60)
                    continue

                episode = episodes.pop(episodes.index(current_episode))

                # A new episode has started; terminate recording
                if self.proc is not None:
                    self.proc.terminate()

                    while not self.proc.poll():
                        self.handler.sxm.log("Waiting for ffmpeg to terminate..")
                        time.sleep(1)

                    self.proc = None
                    self.tag_file(f"{self.output_directory}/{self.current_filename}")

            if self.should_record_episode(episode):
                if (
                    self.proc is None
                    or self.proc is not None
                    and self.proc.poll() is not None
                ):
                    self.rip_episode(episode)

            time.sleep(1)

    def rip_episode(self, episode):
        try:
            filename = time.strftime(
                "%Y-%m-%d_%H_%M_%S_{}.mp3".format(
                    "_".join(episode["mediumTitle"].split())
                )
            )
            self.current_filename = filename

            cmd = "ffmpeg -i http://127.0.0.1:8888/{}.m3u8 -acodec libmp3lame -ac 2 -ab {} {}/{}".format(
                self.channel, self.bitrate, self.output_directory, filename
            )

            self.handler.sxm.log("Executing: {}".format(cmd))
            self.proc = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, shell=False
            )
            self.handler.sxm.log("Launched process: {}".format(self.proc.pid))
        except Exception as e:
            self.handler.sxm.log(
                "Exception occurred in Ripper.rip_stream: {}".format(e)
            )
            self.handler.sxm.log("Tagging file before recovering stream..")
            self.tag_file(f"{self.output_directory}/{self.current_filename}")

    def tag_file(self, filename):
        if self.config == {}:
            return

        playlist = None
        with open(self.config, encoding="utf-8") as f:
            text = f.read()
            playlist = json.loads(text)

        x = "|".join(playlist["tags"].keys())
        playlist_regex = re.compile(x, re.IGNORECASE)
        date_regex = re.compile("(\d{4})-(\d{2})-(\d{2})")
        track_parts = defaultdict(int)

        if not filename.endswith(".mp3"):
            return

        playlist_match = playlist_regex.findall(filename)
        date = next(date_regex.finditer(filename), "")

        if not all([date, playlist_match]):
            return

        playlist_match = playlist_match[0]

        # Increment the track count
        playlist["tags"][playlist_match]["track_count"] += 1

        title = "{} {}".format(
            "".join(date.groups()), playlist["tags"].get(playlist_match).get("artist")
        )

        track_parts[title] += 1

        tag_title = title
        if track_parts.get(title) > 1:
            tag_title += " (Part {})".format(track_parts.get(title))

        self.handler.sxm.log(
            "File: {} | Playlist: {} | Date: {}".format(
                filename, playlist_match, "".join(date.groups())
            )
        )

        mp3 = eyed3.load(filename)
        self.handler.sxm.log(playlist["tags"].get(playlist_match).get("album"))
        mp3.tag.album = playlist["tags"].get(playlist_match).get("album")
        mp3.tag.album_artist = playlist["tags"].get(playlist_match).get("artist")
        mp3.tag.artist = playlist["tags"].get(playlist_match).get("artist")
        mp3.tag.genre = playlist["tags"].get(playlist_match).get("genre")
        mp3.tag.recording_date = "-".join(date.groups())
        mp3.tag.release_date = "-".join(date.groups())
        mp3.tag.title = tag_title
        mp3.tag.track_num = playlist["tags"].get(playlist_match).get("track_count")
        mp3.tag.save()

        with open(self.config, "w") as config:
            config.write(json.dumps(playlist, indent=4))

        self.handler.sxm.log("Track parts")
        self.handler.sxm.log(json.dumps(track_parts, indent=4))


def parse_args():
    args = argparse.ArgumentParser(description="It does boss shit")
    args.add_argument(
        "-u",
        "--user",
        help="The user to use for authentication",
        default=os.environ.get("SIRIUSXM_USER"),
    )
    args.add_argument(
        "-p",
        "--passwd",
        help="The pass to use for authentication",
        default=os.environ.get("SIRIUSXM_PASS"),
    )
    args.add_argument("--port", help="The port to listen on", default=8888, type=int)
    args.add_argument(
        "-c",
        "--channel",
        help="The channel(s) to listen on. Supports multiple uses of this arg",
    )
    args.add_argument(
        "-r", "--rip", help="Record the stream(s)", default=False, action="store_true"
    )
    args.add_argument(
        "-l",
        "--list",
        help="Get the list of all radio channels available",
        action="store_true",
        default=False,
    )
    args.add_argument(
        "-o",
        "--output-directory",
        help="Specify a target directory for dumping (defaults to cwd)",
        default=os.path.abspath("."),
    )

    args.add_argument(
        "-f",
        "--file",
        help="Optional, config file to use",
        default=None
    )

    return args.parse_args()


def get_channel_list(sxm):
    channels = list(
        sorted(
            sxm.get_channels(),
            key=lambda x: (
                not x.get("isFavorite", False),
                int(x.get("siriusChannelNumber", 9999)),
            ),
        )
    )

    l1 = max(len(x.get("channelId", "")) for x in channels)
    l2 = max(len(str(x.get("siriusChannelNumber", 0))) for x in channels)
    l3 = max(len(x.get("name", "")) for x in channels)
    print("{} | {} | {}".format("ID".ljust(l1), "Num".ljust(l2), "Name".ljust(l3)))
    for channel in channels:
        cid = channel.get("channelId", "").ljust(l1)[:l1]
        cnum = str(channel.get("siriusChannelNumber", "??")).ljust(l2)[:l2]
        cname = channel.get("name", "??").ljust(l3)[:l3]
        print("{} | {} | {}".format(cid, cnum, cname))


def main():
    args = parse_args()

    if not os.path.isdir(args.output_directory):
        raise Exception(
            f"The target output directory {args.output_directory} is not a valid directory"
        )

    if args.user is None or args.passwd is None:
        raise Exception(
            "Missing username or password. You can also set these as environment variables "
            "SIRIUSXM_USER, SIRIUSXM_PASS"
        )

    sirius_handler = make_sirius_handler(args)

    if args.list:
        get_channel_list(sirius_handler.sxm)
        sys.exit(0)

    ripper = SiriusXMRipper(sirius_handler, args)

    executor = ThreadPoolExecutor(max_workers=2)
    httpd_thread = executor.submit(start_httpd, sirius_handler)
    ripper_thread = executor.submit(ripper.poll_episodes)

    while True:
        if httpd_thread.done():
            sirius_handler.sxm.log(
                "HTTPD Thread exited/terminated -- result:{}".format(
                    httpd_thread.result()
                )
            )
            httpd_thread = executor.submit(start_httpd, sirius_handler)

        if ripper_thread.done():
            sirius_handler.sxm.log(
                "Ripper Thread exited/terminated -- result:{}".format(
                    ripper_thread.result()
                )
            )
            ripper_thread = executor.submit(ripper.poll_episodes)

        time.sleep(60)


if __name__ == "__main__":
    main()
