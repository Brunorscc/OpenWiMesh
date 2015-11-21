#!/bin/bash
#trafego-controle.sh

TIME=$1
IP=$2
PATH="/home/openwimesh/capturas/$TIME/dump-flows/16n-$IP-dump"

while true:
do
	`date +%s` >> $PATH
	ovs-ofctl dump-flows ofsw0 >> $PATH
	echo "#" >> $PATH
	sleep 5;
done