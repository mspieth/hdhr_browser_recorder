#!/bin/bash

# usage mythtv_recording_started.sh %CARDID% %CHANID% %STARTTIME%

# make sure the max wait time in MythTV for tuning this device is set
# no less that 40000 ms (40 sec), the encoder reboot is slow

log () {
	logger -p local7.info mythbackend $@
}

HERE=`dirname $0`

CardID="$1"
Channel="$2"
StartTime="$3"
File="$4"

log $StartTime "mythtv_recording_started.sh launch"

log $StartTime "recording_started.sh: CardID " $CardID " Channel " $Channel " File " $File

if [ -n "$File" ]; then
	File="--file $File"
fi

File=

lockfile="/tmp/iptvencoder.noboot" # we set this file as a lock to minimize reboots in Live TV mode

Enc_Status=`which mythtv_encoder_status`

if [ -z "$Enc_Status" ]
then
	log $StartTime "recording_started.sh: mythtv_encoder_status is not installed in PATH"
	exit 1
fi

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
		check_process
		if [ ! -e "/tmp/iptvencoder.pid" ]; then
			"$HERE/iprecorder.sh" "$File" &
			PID=$!
			if [ -n "$PID" ]; then
				log "Encoder started successfully"
				echo $PID > /tmp/iptvencoder.pid
				log "started.sh: Cardid $CardID change channel" $?
				sleep 5
				check_process
			else
				log "Encoder was not started successfully"
			fi
		else
			log "Encoder still running"
		fi
		;;
	*)
		log "started.sh: Cardid" $CardID "NO ACTION" $?
		;;
esac
exit 0

