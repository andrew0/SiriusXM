# SiriusXM

This script creates a server that serves HLSstreams for SiriusXM channels.
With an optional configuration file, the recording mode can record shows from
specific channels and even populate ID3 tags on the output file for you.

#### Requirements
Python libraries:
* eyeD3
* requests 
* tenacity

If you wish to record streams, you'll need to have [ffmpeg](https://www.ffmpeg.org/)
installed with [LAME](https://sourceforge.net/projects/lame/) support compiled in.

#### Installation
Install the Python dependencies

`pip install -r requirements.txt`


#### Configuration

You can store your XM credentials as environment variables if you don't want
to use the arg parser. Use `SIRIUSXM_USER` and `SIRIUSXM_PASS`.

```bash
export SIRIUSXM_USER="username"
export SIRIUSXM_PASS="password"
```

If you wish to record shows, read this section
##### Example configuration

The following is an example `config.json`
```json
{
  "bitrate": "160k",
  "shows": [
    "Soul Assassins"
  ],
  "tags": {
    "DJ_Muggs_&_Ern_D": {
        "artist": "DJ Muggs & Ern Dogg",
        "album": "Soul Assassins Radio",
        "genre": "Hip-Hop"
      }
  }
}
```
The `bitrate` (required) can be whatever you wish (i.e. 128k, 192k, 256k). Keep in mind
that a higher bitrate equals a higher file size.

Your `show` (optional) names are matched using a case insensitive regular expression, so you only need to
match the title of your show partially. 

The `tags` (optional) section uses the short title
from the XM API as the key for tagging data. You can get this from the API 
yourself or just add it after you've added a show (the short title is in the
filename). 


## Usage
#### Simple HLS server
`python sxm.py -u myuser -p mypassword`

Then in a player that supports HLS (QuickTime, VLC, ffmpeg, etc) you can
access a channel at http://127.0.0.1:8888/channel.m3u8 where "channel" is
the channel name, ID, or Sirius channel number.

#### Start the server in ripping mode
`python sxm.py -u myuser -p mypassword -c channel -r`

Use the configuration json (`config.json`) to specify bitrate, programs
to record and tagging details. Shows are dumped locally using the short title
of the show which was recorded (i.e. `20180704180000-My_Program.mp3`)

Tagging occurs once the ffmpeg stream has been closed.


#### List all XM channels
`python sxm.py -u myuser -p mypassword -l`

Example output:

```bash
ID                  | Num | Name
big80s              | 8   | 80s on 8
90salternative      | 34  | Lithium
altnation           | 36  | Alt Nation
```
