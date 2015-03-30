# SiriusXM
This script provides SiriusXM live radio playback by creating an HTTP server that serves HLS playlists. Currently, this does not work properly in VLC, but it works fine in QuickTime on OS X and ffmpeg.

To use it, simply change the username and password constants in server.py, then run server.py in your Terminal. To access channels, open an HLS stream with the following format: http://127.0.0.1:9001/CHANNEL_NUMBER_HERE.m3u8. For example, if you wanted to listen to Lithium on channel 34, you would open http://127.0.0.1:9001/34.m3u8.

Currently, this script will only use the 256k AAC stream.