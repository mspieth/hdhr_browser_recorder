#!/bin/bash

sudo modprobe snd-aloop pcm_substreams=1

PROG="google-chrome -start-maximized --use-gl=osmesa6 --enable-webgl --ignore-gpu-blacklist https://watch.foxtel.com.au/app"
PROG="google-chrome --remote-debugging-port=9222 -start-maximized --alsa-output-device=hw:Loopback,0,0 https://watch.foxtel.com.au/app"
#PROG="google-chrome -start-maximized --alsa-output-device=hw:Loopback,0,0 https://google.com.au"
OPTS="+extension RANDR +extension RENDER +extension GLX"
#PROG=xdpyinfo
#PROG=glxinfo
xvfb-run --server-args='-ac -screen 0, 1280x720x24, -extension RANDR, -extension RENDER, -extension GLX' $PROG
