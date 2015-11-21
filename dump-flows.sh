#!/bin/bash
#dump-flows.sh

#TIME=`date +%Y-%m-%d-%H:%M`
sleep 10
IP=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "inet addr:[^ ]*" |cut -d: -f2)
#PATH=`echo "/home/openwimesh/capturas/$TIME/dump-flows/16n-$IP-dump"`


while true;
do
date +%s >> /home/openwimesh/capturas/dump-flows/$IP-flows
ovs-ofctl dump-flows ofsw0 >> /home/openwimesh/capturas/dump-flows/$IP-flows
echo "#" >> /home/openwimesh/capturas/dump-flows/$IP-flows
sleep 5
done