# SiriusXM

![TravisCI Build Status](https://travis-ci.org/infamousjoeg/SiriusXM.svg?branch=feature-travisci)

This script creates a server that serves HLS streams for SiriusXM channels.

## Table of Contents
- [SiriusXM](#siriusxm)
  - [Table of Contents](#table-of-contents)
    - [Authentication](#authentication)
    - [Usage](#usage)
      - [Pre-Requisites](#pre-requisites)
      - [Quick Start](#quick-start)
      - [List SiriusXM Channels](#list-siriusxm-channels)
    - [How to Listen](#how-to-listen)
    - [License](#license)

### Authentication

Authentication is expected in the environment variables `SXM_USERNAME` and `SXM_PASSWORD`.

To automatically set authentication, in an `sxmlogin.cred` file that you create in the root directory, use  this format:

```
SXM_USERNAME=siriusxmusername
SXM_PASSWORD=siriusxmpassword
```

and add them to your environment variables: `source sxmlogin.cred`

### Usage

#### Pre-Requisites

After setting [Authentication](#authentication), you may procede with the following.

#### Quick Start

To use it, pass a port to run the server on.  For example, you start the server by running:

```shell
./sxm.py -p 8888
```

#### List SiriusXM Channels
You can see a list of the channels by setting the -l or --list flag:

```shell
./sxm.py -l
```

### How to Listen

Then in a player that supports HLS (QuickTime, VLC, ffmpeg, etc) you can access a channel at http://127.0.0.1:8888/channel.m3u8 where `channel` is the channel name, ID, or SiriusXM channel number.

I use [VLC](https://www.videolan.org/vlc/index.html) and have included support for auto-launching a SiriusXM channel in the terminal using VLC.

If you know what channel you're looking for, an easy way of searching for info is like:

```shell
./sxm.py -l | grep <channel_name>
```

The one I use the most is:

```shell
./sxm.py -l | grep lithium
```

Then, to auto-launch VLC with the channel selected, it's as easy as:

```shell
./sxm.py -p 8888 --vlc --channel lithium
```

Here's a list of some of the channel IDs:

| Name                              | ID                  |
|-----------------------------------|---------------------|
| The Covers Channel                | 9416                |
| Sports 958                        | 9427                |
| Utah Jazz                         | 9294                |
| Sports 975                        | 9212                |
| VOLUME                            | 9442                |
| HLN                               | cnnheadlinenews     |
| Laugh USA                         | laughbreak          |
| Washington Wizards                | 9295                |
| Carlin's Corner                   | 9181                |
| 70s on 7                          | totally70s          |
| SXM NHL Network Radio             | 8185                |
| Tom Petty Radio                   | 9407                |
| Underground Garage                | undergroundgarage   |
| SiriusXM Spotlight                | 9138                |
| Radio Margaritaville              | radiomargaritaville |
| Cincinnati Reds                   | 9237                |
| Portland Trail Blazers            | 9290                |
| SiriusXM FC                       | 9341                |
| Miami Marlins                     | 9245                |
| SiriusXM Insight                  | 8183                |
| SiriusXM FLY                      | 9339                |
| Red White & Booze                 | 9178                |
| Kids Place Live                   | 8216                |
| New York Islanders                | 9313                |
| New York Rangers                  | 9314                |
| SiriusXM NASCAR Radio             | siriusnascarradio   |
| 1st Wave                          | firstwave           |
| Los Angeles Rams                  | 9203                |
| Houston Rockets                   | 9276                |
| Washington Capitals               | 9324                |
| Joel Osteen Radio                 | 9392                |
| Attitude Franco                   | energie2            |
| Classic Rewind                    | classicrewind       |
| SiriusXM PGA TOUR Radio           | 8186                |
| Miami Heat                        | 9281                |
| 80s on 8                          | big80s              |
| SiriusXM 375                      | 9459                |
| Dallas Stars                      | 9304                |
| Sports 977                        | 9214                |
| Denver Broncos                    | 9155                |
| Hip-Hop Nation                    | hiphopnation        |
| Boston Red Sox                    | 9234                |
| SXM Limited Edition 5             | 9399                |
| SiriusXM Silk                     | 9364                |
| Flow Nación                       | 9185                |
| Miami Dolphins                    | 9162                |
| Sports 983                        | 9327                |
| Viva                              | 8225                |
| Sports 985                        | 9329                |
| Barstool Radio on SiriusXM        | 9467                |
| San Francisco 49ers               | 9202                |
| Sports 992                        | 9336                |
| Arizona Diamondbacks              | 9231                |
| ESPN Xtra                         | 8254                |
| Utopia                            | 9365                |
| RockBar                           | 9175                |
| Road Dog Trucking                 | roaddogtrucking     |
| Colorado Rockies                  | 9239                |
| Colorado Avalanche                | 9303                |
| Real Jazz                         | purejazz            |
| Free Bird: LynyrdSkynyrd          | 9139                |
| Sports 994                        | 9338                |
| Bluegrass Junction                | bluegrass           |
| Sports 986                        | 9330                |
| CBC Radio One                     | cbcradioone         |
| POTUS Politics                    | indietalk           |
| The Groove                        | 8228                |
| American Latino Radio             | 9133                |
| Milwaukee Bucks                   | 9282                |
| Comedy Central Radio              | 9356                |
| Z100/NY                           | 8242                |
| Philadelphia Flyers               | 9316                |
| Chicago Bears                     | 9151                |
| FOX Business                      | 9369                |
| Washington Redskins               | 9206                |
| Oklahoma City Thunder             | 9286                |
| SXM Limited Edition 3             | 9353                |
| SXM Rock Hall Radio               | 9174                |
| Dallas Cowboys                    | 9154                |
| Boston Celtics                    | 9268                |
| Los Angeles Clippers              | 9278                |
| Sports 980                        | 9261                |
| Classic Vinyl                     | classicvinyl        |
| Howard 101                        | howardstern101      |
| TODAY Show Radio                  | 9390                |
| Sway's Universe                   | 9397                |
| ESPN Deportes                     | espndeportes        |
| Houston Texans                    | 9158                |
| MLB Network Radio                 | 8333                |
| Sports 974                        | 9211                |
| La Politica Talk                  | 9134                |
| BB King's Bluesville              | siriusblues         |
| 60s on 6                          | 60svibrations       |
| Sports 991                        | 9335                |
| C-SPAN Radio                      | 8237                |
| Spa                               | spa73               |
| St. Louis Blues                   | 9320                |
| Kansas City Royals                | 9242                |
| CBC Radio 3                       | cbcradio3           |
| SiriusXM 372                      | 9456                |
| The Garth Channel                 | 9421                |
| Howard 100                        | howardstern100      |
| FOX Sports on SiriusXM            | 9445                |
| Sports 979                        | 9216                |
| CBS Sports Radio                  | 9473                |
| RURAL Radio                       | 9367                |
| Sports 984                        | 9328                |
| E Street Radio                    | estreetradio        |
| Pop2K                             | 8208                |
| Indiana Pacers                    | 9277                |
| Korea Today                       | 9132                |
| PRX Public Radio                  | 8239                |
| Philadelphia Phillies             | 9251                |
| Sports 963                        | 9223                |
| Dallas Mavericks                  | 9272                |
| Lithium                           | 90salternative      |
| New Orleans Saints                | 9165                |
| SiriusXM SEC Radio                | 9458                |
| The Joint                         | reggaerhythms       |
| Atlanta Braves                    | 9232                |
| BPM                               | thebeat             |
| Sports 981                        | 9262                |
| Florida Panthers                  | 9307                |
| Sports 969                        | 9229                |
| Willie's Roadhouse                | theroadhouse        |
| SiriusXMU                         | leftofcenter        |
| Family Talk                       | 8307                |
| 80s/90s Pop                       | 9373                |
| FOX News Headlines 24/7           | 9410                |
| Ozzy's Boneyard                   | buzzsaw             |
| Mad Dog Sports Radio              | 8213                |
| Diplo's Revolution Radio          | 9472                |
| SiriusXM ACC Radio                | 9455                |
| Minnesota Timberwolves            | 9283                |
| ONEderland                        | 9419                |
| SXM Limited Edition 9             | 9403                |
| Orlando Magic                     | 9287                |
| Sports 960                        | 9220                |
| Indianapolis Colts                | 9159                |
| San Antonio Spurs                 | 9291                |
| Charlotte Hornets                 | 9269                |
| SiriusXM Stars                    | siriusstars         |
| Phoenix Suns                      | 9289                |
| Canada Laughs                     | 8259                |
| Venus                             | 9389                |
| Sports 989                        | 9333                |
| Minnesota Vikings                 | 9163                |
| Krishna Das Yoga Radio            | 9179                |
| Vancouver Canucks                 | 9323                |
| En Vivo                           | 9135                |
| Buffalo Sabres                    | 9298                |
| Pittsburgh Pirates                | 9252                |
| Sports 978                        | 9215                |
| The Highway                       | newcountry          |
| Kirk Franklin's Praise            | praise              |
| Tampa Bay Buccaneers              | 9204                |
| SiriusXM Rush                     | 8230                |
| Hair Nation                       | hairnation          |
| SiriusXM NFL Radio                | siriusnflradio      |
| The Verge                         | 8244                |
| Milwaukee Brewers                 | 9246                |
| Vegas Stats & Info                | 9448                |
| Petty's Buried Treasure           | 9352                |
| The Loft                          | 8207                |
| Sports 959                        | 9428                |
| The Emo Project                   | 9447                |
| Yacht Rock Radio                  | 9420                |
| SiriusXM Pops                     | siriuspops          |
| The Bridge                        | thebridge           |
| SiriusXM Preview                  | 0                   |
| SiriusXM Hits 1                   | siriushits1         |
| 90s on 9                          | 8206                |
| Cincinnati Bengals                | 9152                |
| Raw Dog Comedy Hits               | rawdog              |
| FOX News Talk                     | 9370                |
| Cleveland Browns                  | 9153                |
| Heart & Soul                      | heartandsoul        |
| Faction Punk                      | faction             |
| Toronto Raptors                   | 9293                |
| SiriusXM Scoreboard               | 8248                |
| Ici Première                      | premiereplus        |
| Cleveland Indians                 | 9238                |
| Chicago White Sox                 | 9236                |
| Los Angeles Chargers              | 9171                |
| New York Knicks                   | 9285                |
| Carolina Hurricanes               | 9299                |
| Montreal Canadiens                | 9310                |
| St. Louis Cardinals               | 9256                |
| Águila                            | 9186                |
| Sports 988                        | 9332                |
| The Beatles Channel               | 9446                |
| New York Yankees                  | 9249                |
| EW Radio                          | 9351                |
| Sports 971                        | 9208                |
| Canadian IPR                      | 9358                |
| SiriusXM Comes Alive!             | 9176                |
| 40s Junction                      | 8205                |
| Arizona Cardinals                 | 9146                |
| Sports 961                        | 9221                |
| Elvis Radio                       | elvisradio          |
| enLighten                         | 8229                |
| Atlanta Hawks                     | 9266                |
| Chicago Cubs                      | 9235                |
| Seattle Mariners                  | 9255                |
| Road Trip Radio                   | 9415                |
| Symphony Hall                     | symphonyhall        |
| SXM Limited Edition 11            | 9405                |
| Latidos                           | 9187                |
| SiriusXM Comedy Greats            | 9408                |
| Sports 982                        | 9326                |
| Sports 957                        | 9426                |
| Detroit Lions                     | 9156                |
| SiriusXM Chill                    | chill               |
| SiriusXM Pac-12 Radio             | 9457                |
| Chicago Blackhawks                | 9302                |
| Cinemagic                         | 8211                |
| SiriusXM Progress                 | siriusleft          |
| Atlanta Falcons                   | 9147                |
| Liquid Metal                      | hardattack          |
| Radio Disney                      | radiodisney         |
| The Blend                         | starlite            |
| Verizon IndyCar Series            | 9207                |
| Toronto Blue Jays                 | 9259                |
| Octane                            | octane              |
| Jam On                            | jamon               |
| The Billy Graham Channel          | 9411                |
| Calgary Flames                    | 9301                |
| Triumph                           | 9449                |
| Sports 966                        | 9226                |
| Houston Astros                    | 9241                |
| ESPNU Radio                       | siriussportsaction  |
| Chicago Bulls                     | 9270                |
| Pearl Jam Radio                   | 8370                |
| Caricia                           | 9188                |
| Brooklyn Nets                     | 9267                |
| Sports 990                        | 9334                |
| Denver Nuggets                    | 9273                |
| El Paisa                          | 9414                |
| New York Jets                     | 9167                |
| Iceberg                           | icebergradio        |
| 70s/80s Pop                       | 9372                |
| The Message                       | spirit              |
| Minnesota Wild                    | 9309                |
| Nashville Predators               | 9312                |
| Memphis Grizzlies                 | 9280                |
| PopRocks                          | 9450                |
| SXM Limited Edition 8             | 9402                |
| Arizona Coyotes                   | 9394                |
| La Kueva                          | 9191                |
| SiriusXM NBA Radio                | 9385                |
| Sports 967                        | 9227                |
| BBC World Service                 | bbcworld            |
| Sports 976                        | 9213                |
| Rumbón                            | 9190                |
| Ici Musique Chansons              | 8245                |
| NPR Now                           | nprnow              |
| KIDZ BOP Radio                    | 9366                |
| Sports 973                        | 9210                |
| SXM Limited Edition 4             | 9398                |
| Velvet                            | 9361                |
| Classic Rock Party                | 9375                |
| Los Angeles Lakers                | 9279                |
| Met Opera Radio                   | metropolitanopera   |
| SXM Limited Edition 6             | 9400                |
| Green Bay Packers                 | 9157                |
| Sacramento Kings                  | 9292                |
| Pittsburgh Steelers               | 9170                |
| Sports 954                        | 9423                |
| Carolina Shag Radio               | 9404                |
| KIIS-Los Angeles                  | 8241                |
| Deep Tracks                       | thevault            |
| Business Radio                    | 9359                |
| Philadelphia Eagles               | 9169                |
| Buffalo Bills                     | 9149                |
| The Spectrum                      | thespectrum         |
| Grateful Dead                     | gratefuldead        |
| Pitbull's Globalization           | 9406                |
| CNN                               | cnn                 |
| Oldies Party                      | 9378                |
| Golden State Warriors             | 9275                |
| CNBC                              | cnbc                |
| Sports 965                        | 9225                |
| The Catholic Channel              | thecatholicchannel  |
| New England Patriots              | 9164                |
| New Orleans Pelicans              | 9284                |
| ESPN Radio                        | espnradio           |
| Bloomberg Radio                   | bloombergradio      |
| The Heat                          | hotjamz             |
| Columbus Blue Jackets             | 9300                |
| Sports 968                        | 9228                |
| Oakland Raiders                   | 9168                |
| Sports 972                        | 9209                |
| Detroit Tigers                    | 9240                |
| Pittsburgh Penguins               | 9318                |
| HBCU                              | 9130                |
| Los Angeles Kings                 | 9308                |
| Ottawa Senators                   | 9315                |
| MSNBC                             | 8367                |
| Outlaw Country                    | outlawcountry       |
| SXM Limited Edition 7             | 9401                |
| Prime Country                     | primecountry        |
| Jason Ellis                       | 9363                |
| Alt Nation                        | altnation           |
| No Shoes Radio                    | 9418                |
| Radio Andy                        | 9409                |
| Baltimore Ravens                  | 9148                |
| San Jose Sharks                   | 9319                |
| San Francisco Giants              | 9254                |
| Siriusly Sinatra                  | siriuslysinatra     |
| New York Giants                   | 9166                |
| Doctor Radio                      | doctorradio         |
| Sports 987                        | 9331                |
| San Diego Padres                  | 9253                |
| Texas Rangers                     | 9258                |
| SiriusXM Turbo                    | 9413                |
| Shade 45                          | shade45             |
| North Americana                   | 9468                |
| Kevin Hart's Laugh Out Loud Radio | 9469                |
| Los Angeles Angels                | 9243                |
| Sports 964                        | 9224                |
| BYUradio                          | 9131                |
| Ici FrancoCountry                 | rockvelours         |
| Washington Nationals              | 9260                |
| SportsCenter                      | 9180                |
| Baltimore Orioles                 | 9233                |
| EWTN Radio                        | ewtnglobal          |
| Vivid Radio                       | 8369                |
| The Village                       | 8227                |
| Carolina Panthers                 | 9150                |
| Escape                            | 8215                |
| Toronto Maple Leafs               | 9322                |
| Studio 54 Radio                   | 9145                |
| New Jersey Devils                 | 9311                |
| Sports 962                        | 9222                |
| Kansas City Chiefs                | 9161                |
| FOX News Channel                  | foxnewschannel      |
| RadioClassics                     | radioclassics       |
| Tennessee Titans                  | 9205                |
| Detroit Red Wings                 | 9305                |
| Telemundo                         | 9466                |
| The Coffee House                  | coffeehouse         |
| Vegas Golden Knights              | 9453                |
| Neil Diamond Radio                | 8372                |
| Minnesota Twins                   | 9247                |
| The Pulse                         | thepulse            |
| HUR Voices                        | 9129                |
| Tampa Bay Rays                    | 9257                |
| SiriusXM Love                     | siriuslove          |
| Rock The Bells Radio              | 9471                |
| Jacksonville Jaguars              | 9160                |
| Sports 953                        | 9422                |
| Philadelphia 76ers                | 9288                |
| Oakland Athletics                 | 9250                |
| Canada Talks                      | 9172                |
| Watercolors                       | jazzcafe            |
| Edmonton Oilers                   | 9306                |
| Elevations                        | 9362                |
| SiriusXM Patriot                  | siriuspatriot       |
| On Broadway                       | broadwaysbest       |
| Detroit Pistons                   | 9274                |
| CNN en Español                    | cnnespanol          |
| Tampa Bay Lightning               | 9321                |
| Indie 1.0                         | 9451                |
| NBC Sports Radio                  | 9452                |
| Celebrate!                        | 9412                |
| Y2Kountry                         | 9340                |
| Los Angeles Dodgers               | 9244                |
| Sports 993                        | 9337                |
| CNN International                 | 9454                |
| Seattle Seahawks                  | 9201                |
| Cleveland Cavaliers               | 9271                |
| Luna                              | 9189                |
| Caliente                          | rumbon              |
| Sports 956                        | 9425                |
| Ramsey Media Channel              | 9443                |
| Faction Talk                      | 8184                |
| Winnipeg Jets                     | 9325                |
| 50s on 5                          | siriusgold          |
| Soul Town                         | soultown            |
| Anaheim Ducks                     | 9296                |
| New York Mets                     | 9248                |
| SiriusXM Urban View               | 8238                |
| Comedy Roundup                    | bluecollarcomedy    |
| Sports 955                        | 9424                |
| Influence Franco                  | 8246                |
| SXM Fantasy Sports Radio          | 8368                |
| CBC Country                       | bandeapart          |
| Boston Bruins                     | 9297                |
| Holiday Traditions                | 9342                |

### License
[MIT](LICENSE.md)