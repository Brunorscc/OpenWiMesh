#!/bin/bash

sleep 120

NODE_LIST="/home/openwimesh/node_list.txt"
IPLOCAL=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "inet addr:[^ ]*" |cut -d: -f2)
#QTD=`cat $NODE_LIST | wc -l`

while true
do
#echo "entrou while"
  i=`shuf -i 0-1 -n1`
  if [ "$i" -eq '1' ]
  then
  	#echo "entrou ping"
  	IP=`shuf -n 1 $NODE_LIST`
  	#echo "IP = $IP"
  	date +%s >> /home/openwimesh/capturas/delay-slowpath/$IPLOCAL
    ping $IP -c 4 >> /home/openwimesh/capturas/delay-slowpath/$IPLOCAL
    #IP=`shuf -n 1 $NODE_LIST`
   # iperf3 -c $IP -p 1999 -b 100K -t 10 
    #iperf3 -c $IP -p 1999 -b 100K -t 10 >> iperf.log
  fi
done