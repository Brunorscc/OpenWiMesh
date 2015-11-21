#!/bin/sh
echo "$(date) - Starting Collector - IFSTAT"
ifstat -n -t -i eth0 -b 5 > collector-ifstat.log &

echo "$(date) - Starting TCPDUMP capture"
tcpdump -n >> collector-tcpdump.log &

bash /home/openwimesh/iperf-client.sh &

bash /home/openwimesh/dump-cpu-mem.sh &

bash /home/openwimesh/dump-flows.sh &
