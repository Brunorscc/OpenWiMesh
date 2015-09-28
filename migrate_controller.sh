#!/bin/bash

PID=$(pidof /home/openwimesh/openwimesh/graphclient/GraphClient)
kill -9 $PID
bash /home/openwimesh/openwimesh/coreemu/customservices/bin/new-openwimesh.sh $1 $2 $3 $4 $5 $6