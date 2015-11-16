#!/bin/bash

PID=$(pidof /home/openwimesh/openwimesh/graphclient/GraphClient)
kill -9 $PID

case "$1" in
	1) bash /home/openwimesh/openwimesh/coreemu/customservices/bin/new-openwimesh.sh $1 $2 $3 $4 $5 $6 $7 $8;;
	2) bash /home/openwimesh/openwimesh/coreemu/customservices/bin/new-openwimesh.sh $1 $2;;
esac