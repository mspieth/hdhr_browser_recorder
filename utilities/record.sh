#!/bin/bash

export DISPLAY=:99.0

function usage()
{
cat <<EOF
Usage: iptv_record.sh [options] channel end_time file"
options:
	--starttime time	24h clock e.g. 20:30
	--list [channel_regex]
EOF
	exit 1
}

NEW=0
STARTTIME=
HLS=hls
while : ; do
	case "$1" in
		--new)
			shift
			NEW=1
			;;
		--starttime)
			shift
			STARTTIME="$1"
			shift
			;;
		-*)
			usage $0
			;;
		*)
			break
			;;
	esac
done

if [ -z "$3" ]; then
	usage
fi

#CHANNEL="EXTINF.*$1"
NAME="$1"
END_TIME="$2"
FILE="$3"

FRAMERATE=50
#FRAMERATE=25

PROFILE=high
PROFILE=high444
#PROFILE=baseline
PIXFMT="-pix_fmt yuv420p"
PIXFMT=

PROGRAM="ffmpeg -f x11grab -video_size 1280x720 -framerate $FRAMERATE -i :99.0+0,0 -f alsa -ac 2 -i plughw:Loopback,1,0 $PIXFMT -c:v libx264 -crf 21 -preset slow -profile $PROFILE -bufsize 5000k -c:a aac -b:a 128k -vsync 1 -y -threads 0"
#PROGRAM="ffmpeg -f x11grab -video_size 1280x720 -framerate 50 -i :99.0+0,0 -f alsa -ac 2 -i plughw:Loopback,1,0 -c:v libx265 -crf 23 -preset slow -bufsize 5000k -c:a aac -b:a 128k -vsync 1 -y -threads 0"

#if [ -z "$ACTUAL_CHANNEL" ]; then
#	echo "Channel $1 does not exist"
#	exit 2
#fi


keep_player_alive() {
	# move mouse so it doesnt fall asleep 
	#   and say "Are you still there?"
	export DISPLAY=:99.0
	while : ; do
		sleep 30m
		xdotool mousemove --sync 1278 0
	done
}

update_length() {
	# update len every so often
	F=`basename $FILE`
	cd `dirname $FILE`
	while : ; do
		sleep 60
		addvideo -op "-channel=506 -manual -no-lookup -no-movie" -title "0DownloadedVideo" -subtitle "$NAME" "$F"
	done
}

cleanup () {
	J="$(jobs -p)"
	[ -n "$J" ] && kill $J
}

start_stream() {
	#xdotool key Escape
	#sleep 0.5
	#xdotool keydown shift
	#xdotool key F5
	#xdotool keyup shift
	#sleep 2
	#xdotool mousemove --sync 200 200
	#sleep 1.0
	#xdotool keydown shift
	#xdotool key F5
	#xdotool keyup shift
	#sleep 1.0
	#xdotool key space
	#sleep 1.0
	#xdotool key F11
	#xdotool mousemove --sync 1278 0
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
	sleep 2.0
	xdotool mousemove --sync 394 142
	sleep 1.0
	xdotool click 1
	sleep 2.0
	#sleep 1.0
	#xdotool key space
	#sleep 1.0
	xdotool key F11
	xdotool mousemove --sync 1278 0
}

stop_stream() {
	export DISPLAY=:99.0
	xdotool key Escape
	sleep 0.5
	xdotool key Escape
	sleep 0.5
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
}

restart_stream() {
while : ; do
	sleep 5h
	xdotool key Escape
	sleep 0.5
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
	sleep 2
	xdotool key space
	sleep 0.5
	xdotool key F11
done
}

if [ -n $DURATION ]; then
	if [ $NEW = 1 ]; then
		rm "$FILE"
	fi
	now=$(date +%s)
	timeToWait=0
	if [ -n "$STARTTIME" ]; then
		startTime=$(date -d "$STARTTIME" +%s)
		timeToWait=$(($startTime - $now))
		date
	fi

	DURATION=
	if [[ $END_TIME =~ ^[0-9]+[smhd]?$ ]]; then
		DURATION="$END_TIME"
		echo "fallback"
	else
		now=$(date +%s)
		endTime=$(date -d "$END_TIME" +%s)
		if [ $? -eq 0 ]; then
			if [ $timeToWait -gt 0 ]; then
				DURATION=$(($endTime - $now - $timeToWait)) 
			else
				DURATION=$(($endTime - $now)) 
			fi
		fi
	fi

	trap cleanup EXIT
	keep_player_alive &

	echo "Recording Channel '$NAME' for $END_TIME ($DURATION secs)"
	if [ $timeToWait -gt 0 ]; then
		echo "Sleeping until $STARTTIME ($timeToWait) Duration is $DURATION"
		sleep $timeToWait
	fi
	echo "Starting Record Duration is $DURATION"

	
	start_stream
	update_length &
	restart_stream &

	timeout --foreground $DURATION $PROGRAM "$FILE" >/dev/null 2>&1
	#timeout --foreground $DURATION $PROGRAM "$FILE"

	stop_stream
fi

exit 0
