#!/bin/bash

# usage:  mythtv_recording_pending.sh %CARDID% %SECS% %CHANID%

log () {
	logger -p local7.info mythbackend -- "$@"
}

lockfile="/tmp/iptvencoder.noboot" # we set this file as a lock to minimize reboots in Live TV mode
Pending_lockfile="/tmp/iptvencoder.pending" # we set this file as a block to STB shutdown when a recording is pending

log "pending.sh: launch" $*

HERE=`dirname $0`

CardID="$1"
Time="$2"
Channel="$3"

# Power on and clear box at the 60 event
# if cardid is 1 change channel 2 sec before the recording in to start

check_process() {
	if [ -e "/tmp/iptvencoder.pid" ]; then
		CPID=$(cat "/tmp/iptvencoder.pid")
		if ! kill -0 $CPID ; then
			rm -f "/tmp/iptvencoder.pid"
		fi
	fi
}

case $CardID in

	2)
		log "Time is $Time"
		if [ "$Time" -ge 35 ] && [ "$Time" -lt 80 ]
		then

			#touch "$Pending_lockfile" # create a lock file to flag the recoerding pending state

			Encoder_status=`mythtv_encoder_status --encoder=$CardID`
			if [ "$Encoder_status" = "Idle" -a ! -f $lockfile ]
			then
				log "pending.sh: Cardid $CardID reset encoder" $?
			else

				log "pending.sh: Cardid $CardID do not reset encoder" $?

			fi
		elif [ "$Time" -le 32 ]
		#elif [ "$Time" -le -32 ]
			# change channel on the 30 sec prestart event and restart encoder
		then
			Channel=$(($Channel % 1000))
			ChannelName=$(grep -A1 -B1 "GuideNumber.*$Channel" $HERE/lineup.json | grep "URL" | cut -d/ -f5 | tr -d '"')
			log "$Channel -> $ChannelName"

			log $(curl -s "http://192.168.1.1:5004/record/$ChannelName")
#			check_process
#			if [ ! -e "/tmp/iptvencoder.pid" ]; then
#				"$HERE/iprecorder.sh" &
#				PID=$!
#				if [ -n "$PID" ]; then
#					log "Encoder started successfully"
#					echo $PID > /tmp/iptvencoder.pid
#					log "pending.sh: Cardid $CardID change channel" $?
#					sleep 5
#					check_process
#				else
#					log "Encoder was not started successfully"
#				fi
#			else
#				log "Encoder still running"
#			fi

		fi
		;;
	*)
		log "pending.sh: Cardid" $CardID "NO ACTION" $?
		;;
esac
exit 0
