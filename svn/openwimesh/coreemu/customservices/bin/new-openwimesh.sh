#!/bin/bash
#
# This script starts all the services needed to OpenWiMesh
#

# default values
OWM_IFACES="eth0"
TYPE=$1
OWM_OFCTL=$2
URI=$3
GLOBAL_OFCTL_IP=$4
GLOBAL_OFCTL_HW=$5
CID=$6
CROSSDOMAIN=$7
MONIT=$8

# read configuration
#[ -f openwimesh.conf ] && . openwimesh.conf


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
PRI_MYIP=$(LANG=C ifconfig ofsw0 | grep 'inet ' | awk '{print $2}' | cut -d: -f2)
PRI_MASK=$(LANG=C ifconfig ofsw0 | grep 'inet ' | awk '{print $4}' | cut -d: -f2)

if [ -x `which invoke-rc.d` ]
then
	DAEMONRESTART=invoke-rc.d
elif [ -x `which service` ]
then
	DAEMONRESTART=service
else
	DAEMONRESTART='/etc/init.d/'
fi

log "Starting OpenVswitch daemon"
log "MONIT = $8"
export OVS_DBDIR=$OVS_LOCALDIR
/etc/init.d/openvswitch-switch stop
rm -f $OVS_DBDIR/conf.db
rm -f $OVS_DBDIR/.conf.db.~lock~
/etc/init.d/openvswitch-switch start

log "cleanup IP addresses from openflow interfaces ($OWM_IFACES)"
for i in $OWM_IFACES; do
	ip addr flush dev $i
	ip -6 addr flush dev $i
done

log "Configuring OpenVSwitch"

log "-> Create a bridge"
ovs-vsctl add-br ofsw0

log "-> Configure openflow controller ($OWM_OFCTL)"
ovs-vsctl set-controller ofsw0 tcp:$OWM_OFCTL:6633
ovs-vsctl set Controller ofsw0 connection_mode=out-of-band
ovs-vsctl set Bridge ofsw0 fail_mode=secure

log "-> Adding ports to openvswitch bridge"
for i in $OWM_IFACES; do
   ovs-vsctl add-port ofsw0 $i
done

log "-> Setting ip on switch ($PRI_MYIP / $PRI_MASK)"
ovs-vsctl set Controller ofsw0 local_ip=$PRI_MYIP
ovs-vsctl set Controller ofsw0 local_netmask=$PRI_MASK

log "-> Disabling packet-ins on real ports"
for i in $OWM_IFACES; do
    # We only allow sending "packet-ins" after being connected to the controller.
    # After being connected to controller, GraphClient will activate packet-ins.
    # TODO: check if this is really necessary
    ovs-ofctl mod-port ofsw0 $i no-packet-in
done

log " TIPO = $TYPE"
if [ "$TYPE" = "1" ]; then
  PRI_MYIP=$OWM_OFCTL
  log "ip = $PRI_MYIP"
  ip addr add $PRI_MYIP/24 dev ofsw0
fi

if [ "$OWM_OFCTL" != "$PRI_MYIP" ]; then
	
	ovsif=$(ovs-ofctl show ofsw0 | egrep -o "[0-9]+\($PRI_IFACE\): addr" | cut -d'(' -f1 | tr -d ' ')
	log "-> Inserting default rules"
	ovs-ofctl add-flow ofsw0 arp,in_port=65534,nw_dst=$OWM_OFCTL,actions=output:$ovsif
	ovs-ofctl add-flow ofsw0 arp,nw_dst=$PRI_MYIP,actions=LOCAL
	ovs-ofctl add-flow ofsw0 tcp,in_port=65534,nw_dst=$OWM_OFCTL,tp_dst=6633,actions=output:$ovsif
	ovs-ofctl add-flow ofsw0 tcp,nw_src=$OWM_OFCTL,nw_dst=$PRI_MYIP,tp_src=6633,actions=LOCAL
fi


for i in $OWM_IFACES; do
   # armengue para pegar as mensagens do graphclient no proprio controller
   # caso contrario ela seria entregue diretamente ao SO, que nao tendo porta
   # aberta pra isso, responderia com ICMP UNREACHABLE
   log "ss: $OWM_OFCTL $PRI_MYIP" 
   if [ "$OWM_OFCTL" = "$PRI_MYIP" ]; then
      GC_DEST_IP="192.168.199.253"
      arp -s $GC_DEST_IP 00:00:00:AA:FF:FE
   fi
   log "Starting GraphClient on iface $i (sending to $GC_DEST_IP:$GC_DEST_PORT)"
   /home/openwimesh/openwimesh/graphclient/GraphClient -w $i -o $GC_DEST_IP:$GC_DEST_PORT -b ofsw0 -E -arp >/dev/null 2>&1 &
done

  #script to periodic dump switches's ovs flow table
  #bash /home/openwimesh/dump-flows.sh $MONIT $PRI_MYIP &

if [ "$OWM_OFCTL" = "$PRI_MYIP" ]; then
   IPADDR=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "inet addr:[^ ]*" |cut -d: -f2)
   HWADDR=$(LANG=C /sbin/ifconfig ofsw0 2>/dev/null | egrep -o "HWaddr [^ ]*" | cut -d" " -f2)
   PRIORITY="10"
   

   ovs-ofctl add-flow ofsw0 idle_timeout=20,tcp,nw_src=$IPADDR,nw_dst=$GLOBAL_OFCTL_IP,tp_dst=47922,actions=mod_nw_dst:$GLOBAL_OFCTL_IP,mod_dl_src:$HWADDR,mod_dl_dst:$CROSSDOMAIN,output:1
   ovs-ofctl add-flow ofsw0 idle_timeout=20,tcp,dl_dst=$HWADDR,nw_src=$GLOBAL_OFCTL_IP,nw_dst=$IPADDR,tp_src=47922,actions=mod_nw_dst:$IPADDR,mod_dl_src:$HWADDR,mod_dl_dst:$HWADDR,LOCAL
   arp -s $GLOBAL_OFCTL_IP $HWADDR
   sleep 5
   log "Starting Openflow Controller with OPENWIMESH app (ipaddr=$OWM_OFCTL, hwaddr=$HWADDR, cid=$CID, priority=$PRIORITY)"
   if [ -z "$DISPLAY" ]; then
      export DISPLAY=:0
   fi
   xterm -T "POX (n1)" -e python $POXDIR/pox.py --verbose log --file=/var/log/openwimesh.log,w --no-default --format="%(asctime)s - %(levelname)s - %(message)s" openwimesh --ofip=$OWM_OFCTL --ofmac=$HWADDR --cid=$CID --priority=$PRIORITY --gcid=0 --ofglobalhw=$GLOBAL_OFCTL_HW --ofglobalip=$GLOBAL_OFCTL_IP --uri=$URI --crossdomain=$CROSSDOMAIN --algorithm=0 --monit=$8 py &
fi
