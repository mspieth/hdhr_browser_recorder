# HD Homerun Browser Recorder

HDHR Browser Recorder is a web automation streaming recorder for use with a PVR application. 
It is specifically targeted at MythTV and provides the necessary scripts
to implement either an iptv recorder or an external recorder.

This is alpha quality.

## Overview
This recorder will automate browser control, allowing ffmpeg to record the screen and audio
to a udp stream. 
* The default port is udp://localhost:55555
* The browser listens on port 5004
* Xvfb is on display :99
* x11vnc port is the first free one. 
This is used for debugging automation or fix up any control issues while recording. 

## Requirements
The following packages are required
* python 3.7 or greater
* pipenv
* xvfb
* x11vnc
* ffmpeg
* google-chrome (stable or other)

Also requires passwordless sudo to execute modprobe for installing snd-aloop. 
You will have to disable pulseaudio for this device otherwise there is contention
for this resource.

## Installing
* `git clone ...`
* `cd hdhr_browser_recorder`
* `pipenv --three install`

## Development
I use pycharm. Choose the virtualenv appropriately after pipenv install
### Add extra packages
* `pipenv install <package>`

## Running

Install pipenv and run in a `screen` within `pipenv shell`
* `screen -S recorder`
* reattach with `screen -xr recorder`

Run service:
* `./hdhr_browser_recorder.py`

Change states:
* `curl "http://localhost:5004/play/FOX%20SPORTS%20506"`
* `curl "http://localhost:5004/record/FOX%20SPORTS%20506"`
* `curl "http://localhost:5004/off"`
* `curl "http://localhost:5004/stop"`

There are other variations. See the main file for more path options.

## Integration with MythTV
There are 2 ways to do this
* iptv
  * Create a program list m3u file and import is. See example in utilities.
  * Get a guide. webgrabplus is good for this. Make sure the channel names are correct.
* externalrecorder
  * Guide is the same
  * Import program list **TBD**.
  * use netcat to capture the udp stream to stdout.
  
## Caveats
* The web automation side currently only implements foxtel which requires 
a username and password for your account. 
* This is also not 100% robust with pop-ups and other variations TBD.
* HDHR HTTP stream URL is untested.
* HDHR tcp interface is not fully working. UDP discovery is working.
* Lots of TODOs to make it better and a bit more provider generic.
