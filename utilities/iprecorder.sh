#!/bin/bash

export DISPLAY=:99.0

log () {
	logger -p local7.info mythbackend $@
}

log "starting iprecorder"

function usage()
{
cat <<EOF
Usage: iptv_record.sh [options] channel end_time file"
options:
	--starttime time	24h clock e.g. 20:30
	--list [channel_regex]
	--ipaddr [addr]         i.e. 192.168.1.1:55555
	--test                  test browser control
	--file [filename]       output to file insead of udp
EOF
	exit 1
}

RECORDING_PATH="/data/mythtv/recordings"
NEW=0
STARTTIME=
HLS=hls
TEST=0
IPADDR="192.168.1.1:55555"
FILE=
export LONGSLEEP=5h
TESTDURATION=15s
export DISPLAY=":99"
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
		--test)
			TEST=1
			export LONGSLEEP=30s
			export TESTDURATION=50s
			shift
			;;
		--ipaddr)
			shift
			IPADDR="$1"
			shift
			;;
		--file)
			shift
			FILE="$1"
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

#if [ -z "$3" ]; then
#	usage
#fi

FRAMERATE=50
#FRAMERATE=25

PROFILE=high
PROFILE=high444
#PROFILE=baseline
PIXFMT="-pix_fmt yuv420p"
PIXFMT=
#TUNE="-tune zerolatency"
THREAD_QUEUE="-thread_queue_size 32"
#OUTPUT_FRAMERATE="-r 25"
PRESET=medium

# -mpegts_transport_stream_id 0x0001 -mpegts_service_id 0x0bba -mpegts_start_pid 0x0bba -muxrate 11M
# -muxrate 1500k # for 25fps?
# -f mpegts -muxrate 5000k -flags cgop -sc_threshold 500
# -mpegts_flags resend_headers -f mpegts -muxrate 384k -flags cgop -sc_threshold 500 -mpegts_original_network_id 12293 -mpegts_service_id 7 -mpegts_pmt_start_pid 95 -streamid 0:96 -streamid 1:97 -mpegts_service_type 0x02 -metadata service_provider="MEDIANOV" -metadata service_name="Radio Galileo" -metadata service_type=0x02

# fmpeg -i input -c copy -f mpegts \
#	-mpegts_original_network_id 0x1122 \
#	-mpegts_transport_stream_id 0x3344 \
#	-mpegts_service_id 0x5566 \
#	-mpegts_service_type 0x1 \
#	-mpegts_pmt_start_pid 0x1500 \
#	-mpegts_start_pid 0x150 \
#	-metadata service_provider="Some provider" \
#	-metadata service_name="Some Channel" \
#	-tables_version 5 \
#	sample.ts 

PROGRAM="ffmpeg -re -f x11grab -video_size 1280x720 -framerate $FRAMERATE $THREAD_QUEUE -i :99.0+0,0 -f alsa -ac 2 -i plughw:Loopback,1,0 $PIXFMT -c:v libx264 -crf 21 $GOP -preset $PRESET -profile $PROFILE $TUNE -bufsize 10000k $OUTPUT_FRAMERATE -c:a aac -b:a 256k -vsync 1 -y -threads 0"
#PROGRAM="ffmpeg -threads=0 -re -f x11grab -video_size 1280x720 -framerate $FRAMERATE -i :99.0+0,0 -f alsa -ac 2 -i plughw:Loopback,1,0 $PIXFMT -c:v libx264 -crf 21 -preset slow -profile $PROFILE $TUNE -bufsize 5000k -c:a aac -b:a 128k -vsync 1 -y"
#PROGRAM="ffmpeg -re -f x11grab -video_size 1280x720 -framerate 50 -i :99.0+0,0 -f alsa -ac 2 -i plughw:Loopback,1,0 -c:v libx265 -crf 23 -preset slow -bufsize 5000k -c:a aac -b:a 128k -vsync 1 -y -threads 0"

#if [ -z "$ACTUAL_CHANNEL" ]; then
#	echo "Channel $1 does not exist"
#	exit 2
#fi


keep_player_alive() {
	# move mouse so it doesnt fall asleep 
	#   and say "Are you still there?"
	#export DISPLAY=:99.0
	while : ; do
		sleep 30m
		xdotool mousemove --sync 1278 0
	done
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
	xdotool key Escape
	sleep 1
	xdotool key Escape
	sleep 1
	xdotool key Escape
	sleep 1
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
	sleep 3.0
	# click LiveTV top menu
	xdotool mousemove --sync 394 142
	sleep 1.0
	xdotool click 1
	sleep 3.0
	xdotool mousemove --sync 200 200
	sleep 1.0
	#sleep 1.0
	#xdotool key space
	#sleep 1.0
	xdotool key F11
	xdotool mousemove --sync 1278 0
}

stop_stream() {
	#export DISPLAY=:99.0
	xdotool key Escape
	sleep 1
	xdotool key Escape
	sleep 1
	xdotool key Escape
	sleep 1
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
}

restart_stream() {
while : ; do
	sleep $LONGSLEEP
	xdotool key Escape
	sleep 1
	xdotool keydown shift
	xdotool key F5
	xdotool keyup shift
	sleep 3
	# already playing here
	#xdotool key space
	#sleep 0.5
	xdotool key F11
done
}

cleanup () {
	log "iprecorder: cleanup handler"
	J="$(jobs -p)"
	[ -n "$J" ] && kill $J
	stop_stream
}

trap cleanup EXIT
keep_player_alive &

start_stream
restart_stream &

#ERR_OUTPUT=">/dev/null 2>&1"
#ERR_OUTPUT=

BUFSIZE=$[1024*1024]
BUFSIZE=65535
log "iprecorder: running ffmpeg"
if [ "$TEST" == "0" ]; then
	if [ -n "$FILE" ]; then
		$PROGRAM "$RECORDING_PATH"/"$FILE" #>/dev/null 2>&1
	else
		$PROGRAM -flush_packets 0 -f mpegts "udp://$IPADDR?pkt_size=1316&buffer_size=$BUFSIZE" #>/dev/null 2>&1
	fi
else
	sleep $TESTDURATION
fi

trap - EXIT
cleanup

log "iprecorder: exiting"
exit 0
