#!/bin/bash

# usage: mythtv_recording_finished.sh %CARDID% %CHANID% %STARTTIME% 

log () {
	logger -p local7.info mythbackend $@
}

CardID="$1" 
Channel="$2"
StartTime="$3"

log $StartTime "finished.sh: launch" $*
log $StartTime "recording_finished.sh: CardID" $CardID "Channel " $Channel

ckfile="/tmp/iptvencoder.noboot" # we set this file as a lock to minimize reboots in Live TV mode
Pending_lockfile="/tmp/iptvencoder.pending" # we set this file as a block to STB shutdown when a recording is pending
Sleep_Time=300 # delay for checking if we should power down the STB in seconds
Sleep_Time=30 # delay for checking if we should power down the STB in seconds

case $CardID in

2)

	Encoder_status=`mythtv_encoder_status --encoder=$CardID`

	# Clear the lock if we find we're not in WatchingLiveTV mode. This is a bit of a kludge, but it's the best solution I have. 
	# The big problem will be if we go from WatchingLiveTV to something else and back to WatchingLiveTV 
	# in a short time window we'll end up resetting the encoder more than needed. We really need a LiveTV ended event action

	if [ "$Encoder_status" != "WatchingLiveTV" ]
	then
		rm -f "$lockfile" "$Pending_lockfile"
	fi

	if [ "$Encoder_status" = "Idle" ]
	then
		sleep $Sleep_Time # wait a few minutes to see if we should turn off the STB
		Encoder_status=`mythtv_encoder_status --encoder=$CardID`
		#if [ "$Encoder_status" = "Idle" -a ! -f $Pending_lockfile ] # if we're still idle and a recoding is not pending shut off the STB
		if [ "$Encoder_status" = "Idle" -a ! -f $Pending_lockfile ] # if we're still idle and a recoding is not pending shut off the STB
		then

			####### update the STB Device OFF  command as needed #######    
			PID=$(cat /tmp/iptvencoder.pid)
			if [ -n "$PID" ]; then
				kill $PID
				log "encoder was killed"
			else
				log "there was no encoder to kill"
			fi
			rm -f /tmp/iptvencoder.pid
			############################################################

			log $StartTime "finished.sh: Cardid $CardID, time $Sleep_Time - Turn Off Device"

		else # if we're not still idle do nothing
			log $StartTime "finished.sh: Cardid $CardID, time $Sleep_Time - Do Not Turn Off Device"
		fi
	fi
	;; 
*)

	log $StartTime "finished.sh: Cardid $CardID NO ACTION"
	;;

esac
exit 0

