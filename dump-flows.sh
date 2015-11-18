#!/bin/bash
#dump-flows.sh

#TIME=`date +%Y-%m-%d-%H:%M`
IP=$1
#PATH=`echo "/home/openwimesh/capturas/$TIME/dump-flows/16n-$IP-dump"`

while true;
do
date +%s >> /home/openwimesh/capturas/dump-flows/16n-$IP-dump
ovs-ofctl dump-flows ofsw0 >> /home/openwimesh/capturas/dump-flows/16n-$IP-dump
echo "#" >> /home/openwimesh/capturas/dump-flows/16n-$IP-dump
sleep 30
done