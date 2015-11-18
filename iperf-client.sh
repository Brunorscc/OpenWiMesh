#!/bin/bash

NODE_LIST="/home/openwimesh/node_list.txt"
#QTD=`cat $NODE_LIST | wc -l`

while true
do
  i=`shuf -i 0-1 -n1`
  if [ "$i" = '1' ]
  then
  	IP=`shuf -n 1 $NODE_LIST`
    #ping $IP -c 4
    #iperf3 -c $IP -p 1999 -b 100K -t 10 &> /dev/null
    iperf3 -c $IP -p 1999 -b 100K -t 10 >> iperf.log
  fi
  sleep 10
done