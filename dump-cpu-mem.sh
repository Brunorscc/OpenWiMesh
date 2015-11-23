#!/bin/bash
#script dump cpu&mem from nodes

#TYPE=`ps -C python -o %cpu,%mem,cmd --no-header | wc -l`
sleep 30
IP=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "inet addr:[^ ]*" |cut -d: -f2)
LOCAL="/home/openwimesh/capturas/dump-cpu-mem/$IP"

while true
do
	TEMP=""
	A=$(ps -C GraphClient -o %cpu,%mem,cmd --no-header)
	if [ ! -z "$A" ]
	then
TEMP="$TEMP$A"
	fi

	B=$(ps -C ovs-vswitchd -o %cpu,%mem,cmd --no-header | awk 'NR==2')
	if [ ! -z "$B" ]
	then
TEMP="$TEMP
$B"
	fi

	C=$(ps -C xterm -o %cpu,%mem,cmd --no-header)
	if [ ! -z "$C" ]
	then
TEMP="$TEMP
$C"
	fi

	D=$(ps -C python -o %cpu,%mem,cmd --no-header)
	if [ ! -z "$D" ]
	then
TEMP="$TEMP
$D"
	fi

	TYPE=`ps -C python -o %cpu,%mem,cmd --no-header | wc -l`
	case "$TYPE" in
		0)
			tipo="switch"
			;;
		1)
			tipo="ctrl"
			;;
		2)
			tipo="gctrl"
			;;
	esac

	echo -e "`date +%s`\n$TEMP" >> "$LOCAL-$tipo"
			sleep 30

done