#!/bin/bash
#
# This script starts all the services needed to OpenWiMesh
#

# default values
OWM_IFACES="eth0"
OWM_OFCTL="192.168.199.254"
OWM_OFCTL_SLAVE="192.168.199.9"

# read configuration
[ -f openwimesh.conf ] && . openwimesh.conf

OVS_LOCALDIR="/var/lib/openvswitch"
LOG=openwimesh_startup.log
GC_DEST_IP=$OWM_OFCTL
GC_DEST_PORT=1111
POXDIR=/home/openwimesh/pox

function log {
   echo "$(date +%Y-%m-%d,%H:%M) $1" >> $LOG
}

# only continue if we have interfaces to manage
[ -n "$OWM_IFACES" ] || exit 0

if [ ! -x /usr/sbin/ovs-vswitchd ]; then
	log "OVS: openvswitch not found (maybe not installed?)"
	exit 1
fi

# the interface used to connect to openflow controller is the first one
PRI_IFACE=${OWM_IFACES%% *}
PRI_MYIP=$(LANG=C ifconfig $PRI_IFACE | grep 'inet ' | awk '{print $2}' | cut -d: -f2)
PRI_MASK=$(LANG=C ifconfig $PRI_IFACE | grep 'inet ' | awk '{print $4}' | cut -d: -f2)


if [[ "$OWM_OFCTL" = "$PRI_MYIP" || "$OWM_OFCTL_SLAVE" = "$PRI_MYIP" ]]; then
#if [ "$OWM_OFCTL" = "$PRI_MYIP" ]; then
   IPADDR=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "inet addr:[^ ]*" |cut -d: -f2)
   HWADDR=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "HWaddr [^ ]*" | cut -d" " -f2)
   log "Starting Openflow Controller with OPENWIMESH app (ipaddr=$IPADDR, hwaddr=$HWADDR)"
   if [ -z "$DISPLAY" ]; then
      export DISPLAY=:0
   fi
   xterm -T "POX (n1)" -e python $POXDIR/pox.py --verbose log --file=/var/log/openwimesh.log,w --no-default --format="%(asctime)s - %(levelname)s - %(message)s" openwimesh --ofip=$IPADDR --ofmac=$HWADDR --algorithm=0 py &
fi
