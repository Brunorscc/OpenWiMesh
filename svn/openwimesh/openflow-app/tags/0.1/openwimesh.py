"""
   OpenWiMesh - Framework for Software Defined Wireless Mesh Networks
   Copyright (C) 2013-2014  GRADE - http://grade.dcc.ufba.br

   This file is part of OpenWiMesh.

   OpenWiMesh is free software: you can redistribute it and/or modify
   it under the terms of the GNU Affero General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   OpenWiMesh is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU Affero General Public License
   along with OpenWiMesh.  If not, see <http://www.gnu.org/licenses/>.

   Linking this library statically or dynamically with other modules is
   making a combined work based on this library.  Thus, the terms and
   conditions of the GNU Affero General Public License cover the whole
   combination.

   As a special exception, the copyright holders of this library give you
   permission to link this library with independent modules to produce an
   executable, regardless of the license terms of these independent
   modules, and to copy and distribute the resulting executable under
   terms of your choice, provided that you also meet, for each linked
   independent module, the terms and conditions of the license of that
   module.  An independent module is a module which is not derived from
   or based on this library.  If you modify this library, you may extend
   this exception to your version of the library, but you are not
   obligated to do so.  If you do not wish to do so, delete this
   exception statement from your version.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.addresses import IPAddr, EthAddr
import pox.lib.packet as packet
from pox.lib.recoco import Timer
import time
import thread
import re
from net_graph import NetGraph
from gnet_graph import GNetGraph
from acl import ACL
from networkx import draw_networkx_nodes
from networkx import draw_networkx_edges
from networkx import draw_networkx_labels
from networkx import draw_networkx_edge_labels
from networkx import circular_layout as layout
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import ipaddress
import os
import random
import Pyro4
from threading import Thread

log = core.getLogger()
Pyro4.config.COMMTIMEOUT = 1.0
# time between arp-resquests that we don't reply again
ARP_REQ_DELAY=10

# MONITORING FILES
#f_flu = open("dumpfluxos.txt", "w")
#f_flu.write("Experiment,Switch,SRC_IP,DST_IP,SRC_PORT,DST_PORT,Packet_Count,Byte_Count,Duration_Sec,Duration_Nsec,Delta_Packet_Count,Delta_Byte_Count,Delta_Duration_Sec,Delta_Duration_Nsec\n")
#f_flu.flush()
        
#f_lat = open("latencia.txt", "w")
#f_lat.write("Switch,Timestamp,RTT\n")
#f_lat.flush()

#f_conv = open("tempo_convergencia.txt", "w")


def handle_PacketIn_Function (self, event):
        """
        Handles packet in messages from some switch
        """
        ether_pkt = event.parse()
        dpid = dpidToStr(event.dpid)


        sw_mac = self.net_graph.get_by_attr('dpid', dpid)
        if sw_mac is None:
            log.debug("INVALID-DPID: %s" % (dpid))
        #    self.net_graph.print_nodes(info=dpid)
        #else:
        #    log.debug("VALID-DPID: %s" % (dpid))

        # Check blacklist
        if not self.acl.is_allowed(receiver=sw_mac, sender=str(ether_pkt.src)):
            #TODO: add flow to drop packets
            log.debug("BLACKLIST: in %s src %s dst %s type %s" %
                (sw_mac, ether_pkt.src, ether_pkt.dst, ether_pkt.type))
            return

        # Acts as a learning switch, using source address and port to
        # update address/port table of that switch
        if sw_mac in self.net_graph:
            self.net_graph.node[sw_mac]['fdb'][str(ether_pkt.src)] = event.port

        # avoid handle packets that are not broadcast and are not to the switch which sent the "packet-in"
        # (interfaces in promiscuous mode will receive these messages)
        #print "event.port = %s" % event.port

        

        if event.port != of.OFPP_LOCAL and ether_pkt.dst != EthAddr(sw_mac) and ether_pkt.dst != EthAddr('ff:ff:ff:ff:ff:ff'):
            print "ta que pariu"
            ipsrc = 'None'
            ipdst = 'None'
            protoip = 'None'
            ip = ether_pkt.find('ipv4')
            if ip is not None:
                ipsrc = str(ip.srcip)
                ipdst = str(ip.dstip)
                protoip = ip.protocol
            log.debug("Dropping packet that may cause a loop, received in %s (macsrc=%s macdst=%s ipsrc=%s ipdst=%s prot=%s)" % (dpid, ether_pkt.src, ether_pkt.dst,ipsrc, ipdst, protoip))
            self._drop(event, idle_timeout=300, hard_timeout=600)
            self._drop_all(event, idle_timeout=0, hard_timeout=0)
            return

        ## try to update ip addr of node the node
        #if event.port == of.OFPP_IN_PORT and ether_pkt.find('ipv4'):
        #    ip = ether_pkt.find('ipv4')
        #    log.debug("=====>>>>>> Set IP-addr of node %s => %s" % (sw_mac, ip.src))
        #    #self.net_graph.set_node_ip(sw_mac, ip.src)

        if ether_pkt.type == packet.ethernet.ARP_TYPE:
            
            arp_pkt = ether_pkt.payload
            if arp_pkt.opcode == packet.arp.REQUEST:
                self._handle_arp_req(event, arp_pkt)
            elif arp_pkt.opcode == packet.arp.REPLY:
                # TODO: what should we do?
                print "era um arp-reply para %s" % ether_pkt.dst
                log.debug("Packet-In of an ARP-Reply: [%s -> %s] %s is at %s" %
                        (ether_pkt.src, ether_pkt.dst, arp_pkt.protodst,
                            arp_pkt.hwdst))
                self._drop(event)
            else:
                self._drop(event)
        elif ether_pkt.type == packet.ethernet.IP_TYPE:
            ip_pkt = ether_pkt.find('ipv4')
            if ip_pkt.protocol == packet.ipv4.UDP_PROTOCOL:
                udp = ip_pkt.find('udp')
                if udp.dstport == 1111:
                    # Format: Interface | Mac Associado | sinal em dBm | Traffic Bytes | Tx speed | SINR speed
                    # record separator: ;
                    # Example: wlan0|00:1c:bf:7c:4b:10|-78|134539566|36.0|12.0
                    pattern = "(\w+)\|([^|]+)\|([\d-]+)\|(\d+)\|([\d\.]+)\|([\d\.]+)"
                    assoc_list = []
                    if not udp.payload:
                        log.debug("WARNING: null packet 1111/UDP (graphClient")
                        self._drop(event)
                        return
                    for s in udp.payload.split(';'):
                        result = re.match(pattern, s)
                        if result:
                            assoc_list.append(result.groups())
                        else:
                            log.debug("WARNING: malformed packet 1111/UDP (graphClient)")
                    if len(assoc_list) > 0:
                        sw = self.net_graph.get_by_attr('dpid', dpidToStr(event.dpid))
                        assoc_list = [node for node in assoc_list
                                        if self.acl.is_allowed(sw, node[1])]
			if not self.net_graph.get_node_edges_update_state(sw):
			    self.ini_topology_up_count += 1
                            log.debug("Topology UP from %s (%s) - time from startup: %.0f" % (sw, self.ini_topology_up_count, time.time() - self.startup_time))
				
                        #log.debug("Nodes: %s" % self.net_graph.nodes(data=True))
                        #log.debug("Edges: %s" % self.net_graph.edges(data=True))
                        self.net_graph.update_edges_of_node(sw, assoc_list)
                        
                        try:
                            cid = self.net_graph.get_cid_ofctl()
                            th = Thread(target=self.gnet_graph.update_edges_of_node, args=(cid,sw, assoc_list,))
                            th.start()
                        except Exception as e:
                            log.debug("Error update gnet edges (%s)" % e)
                        
                        log.debug("Update graph from graphClient() in %s: %s" %
                                (sw, assoc_list))
                        #print "its me"
                else:
                    print "outro udp"
                    self._handle_tcp_udp(event, ip_pkt)
            elif ip_pkt.protocol == packet.ipv4.TCP_PROTOCOL:
                tcp = ip_pkt.find('tcp')
                #print "chegou um tcp"
                if tcp.dstport == 6633:
                    # TODO: rule expired on communication node to controller
                    pass
                elif tcp.srcport == 6633:
                    # TODO: rule expired on communication controller to node
                    pass
                else:
                    self._handle_tcp_udp(event, ip_pkt)
            elif ip_pkt.protocol == packet.ipv4.ICMP_PROTOCOL:
                self._handle_icmp(event, ip_pkt)
            else:
                log.debug("Unknow IP protocol %s" % (ip_pkt.protocol))
                self._drop(event)
        else:
            log.debug("Unknow packet type[%s -> %s] ethertype: %s" %
                    (ether_pkt.src, ether_pkt.dst, ether_pkt.type))

   
class PathHandler():
    def __init__(self):
        self.paths = {}

    def match2index(self, match):
        if 'nw_src' not in match or 'nw_dst' not in match:
            return None
        return "%s-%s" % (match['nw_src'],match['nw_dst'])

    # TODO: delele expired paths...
    def add(self, match, path):
        index = self.match2index(match)
        if index is None:
            return
        self.paths[index] = {'match' : match, 'path' : path}

    def __contains__(self, match):
        index = self.match2index(match)
        return index in self.paths

    def show(self, sep='\n'):
        outstr = ''
        for k in self.paths:
            outstr += 'Match: ' + str(self.paths[k]['match']) + '; '
            outstr += 'Path: ' + str(self.paths[k]['path'])
            outstr += sep
        return outstr


class openwimesh (EventMixin):
    netgraph = None
    gnetgraph = None
    directlyconnectednodes = None
    addnode_time = {}
    show_graph_time_stamp = 0
    gshow_graph_time_stamp = 0
    show_graph_node_count = 0
    gshow_graph_node_count = 0
    show_layout = None
    gshow_layout = None
    show_ani = None
    gshow_ani = None
    globalofctluri = None
    dropfake = None
    fakesw = None
    startuptime = 0
    monit_path = 0
    f_lat = None
    f_conv = None

    #f_lat = open("/home/openwimesh/latencia/%s-latencia-ctrl-%s.txt" % (monit, ofip), "w")
    #f_lat.write("Switch,Timestamp,RTT\n")
    #f_lat.flush()

    #f_conv = open("/home/openwimesh/monit/%s/tempo_convergencia-%s.txt" % (monit, ofip), "w")

    @classmethod
    def who_is_globalctl(cls):
       print "The global controller is %s %s " % ( openwimesh.netgraph.get_ip_global_ofctl(), openwimesh.netgraph.get_hw_global_ofctl() )

    @classmethod
    def make_ofctl(cls,new_ofctl_hw):#self.gnet_graph.add_add_becoming_ofctl(new_ofctl_hw)
        #time.sleep(1)
        try:
            sw_ip = openwimesh.netgraph.get_node_ip(new_ofctl_hw)
            new_ofctl_ip = openwimesh.gnetgraph.get_ofctl_free_ip()
        except Exception as e:
            log.debug("falha receber IP do novo controlador %s",e)
            openwimesh.gnetgraph.del_becoming_ofctl(new_ofctl_hw)
            return 

        try:
            print "%s is free" % new_ofctl_ip
            ofctl_ip = openwimesh.netgraph.get_ip_ofctl()
            path = openwimesh.gnetgraph.path(ofctl_ip,sw_ip)
            print "global path %s -> %s -> %s" % (ofctl_ip,path,sw_ip)
            i = path.index(new_ofctl_hw)
            crossdomain_sw = path[i-1]
        except Exception as e:
            log.debug("falha receber PATH do novo controlador %s",e)
            openwimesh.gnetgraph.del_becoming_ofctl(new_ofctl_hw)
            return 

        openwimesh.netgraph.add_route_ins(sw_ip, crossdomain_sw,new_ofctl_hw)#destino ip do sw
        openwimesh.netgraph.add_route_ins(new_ofctl_ip, crossdomain_sw,new_ofctl_hw)#destino ip do controlador

        try:
            global_ofctl_ip = openwimesh.gnetgraph.get_ip_addr()
            global_ofctl_hw = openwimesh.gnetgraph.get_hw_addr()
            cid = openwimesh.gnetgraph.get_cid_free()
        except Exception as e:
            log.debug("falha receber IP do controlador global %s",e)
            openwimesh.gnetgraph.del_becoming_ofctl(new_ofctl_hw)
            return 

        now = time.time()
        openwimesh.f_conv.write("NEW-CONTROLLER: %s,%f,%f\n" % ( new_ofctl_hw , now , now - openwimesh.startuptime))
        openwimesh.f_conv.flush()

        log.debug("PARMETROS: %s %s %s %s %s %s %s" % (sw_ip, new_ofctl_ip, openwimesh.globalofctluri, global_ofctl_ip, global_ofctl_hw, cid, crossdomain_sw))

        try:
            os.system("bash /home/openwimesh/novo-controlador.sh 1 %s %s %s %s %s %s %s %s" % (sw_ip, new_ofctl_ip, openwimesh.globalofctluri, global_ofctl_ip, global_ofctl_hw, cid, crossdomain_sw, time.time()))
        except Exception as e:
            log.debug("falha ao criar controlador remoto %s",e)
            openwimesh.gnetgraph.del_becoming_ofctl(new_ofctl_hw)
         #   return 
        #os.system("bash /home/openwimesh/novo-controlador.sh 192.168.199.4 192.168.199.252 PYRO:global_ofcl_app@192.168.199.254:47922 192.168.199.254 00:00:00:aa:00:00 1 00:00:00:aa:00:02 ")
        try:
            if sw_ip in openwimesh.fakesw:
                openwimesh.dropfake[sw_ip] = []
                openwimesh.dropfake[sw_ip].append(openwimesh.fakesw[sw_ip])
                now = time.time()
                openwimesh.dropfake[sw_ip].append(now)
                del openwimesh.fakesw[sw_ip]
        except Exception as e:
            log.debug("erro fake (%s)",e)

    @classmethod
    def add_node(cls,new_hw, new_ip, border_hw):
        openwimesh.netgraph.add_node(new_hw, new_ip)
        openwimesh.netgraph.add_edge(new_hw, border_hw, weight=10*NetGraph.DEFAULT_WEIGHT, wired=True)
        openwimesh.netgraph.add_edge(border_hw, new_hw, weight=10*NetGraph.DEFAULT_WEIGHT, wired=True)

    @classmethod
    def show_graph(cls, attr='weight', node_attr='name', title='Wireless Mesh Network'): # attr is the name of edge attribute
        figure = plt.figure()
        plt.ion()

        def update_image(cls):
            log.debug("Show Graph: Updating image")

            if openwimesh.netgraph:
                if openwimesh.show_graph_time_stamp < openwimesh.netgraph.time_stamp:
                    plt.clf() # clear old image
                    plt.title(title) # reinsert title

                    if openwimesh.show_graph_node_count != openwimesh.netgraph.number_of_nodes():
                        log.debug("Show Graph:  Calc New Layout")
                        # generate new layout for graph
                        openwimesh.show_layout = layout(openwimesh.netgraph)
                        openwimesh.show_graph_node_count = openwimesh.netgraph.number_of_nodes()

                    log.debug("Show Graph:  New Time Stamp: " + str(openwimesh.netgraph.time_stamp))
                    openwimesh.show_graph_time_stamp = openwimesh.netgraph.time_stamp 
                    # draw nodes
                    draw_networkx_nodes(openwimesh.netgraph,openwimesh.show_layout,node_size=1500)
                    # draw edges
                    draw_networkx_edges(openwimesh.netgraph,openwimesh.show_layout)
                    # getting node labels
                    labels = dict([(node,node_attributes[node_attr]) for
                        node,node_attributes in openwimesh.netgraph.nodes(data=True)])
                    # draw node labels
                    draw_networkx_labels(openwimesh.netgraph,openwimesh.show_layout,labels=labels)
                    # getting edges labels
                    labels=dict([((source,target), edges_attributes[attr]) for
                        source,target,edges_attributes in
                        openwimesh.netgraph.edges(data=True)])
                    # draw edges labels
                    draw_networkx_edge_labels(openwimesh.netgraph,openwimesh.show_layout,
                            edge_labels=labels,label_pos=0.18)

        openwimesh.show_ani = animation.FuncAnimation(figure, update_image,
                blit=False, interval=10000)
        plt.title(title) # insert title
        plt.show()

    @classmethod
    def show_global_graph(cls, attr='weight', node_attr='name', title='Wireless Mesh Network - Global View'): # attr is the name of edge attribute
        openwimesh.gshow_graph_time_stamp = 0
        figure = plt.figure()
        plt.ion()

        def update_image(cls):
            log.debug("Show Global Graph: Updating image")
            gnetg = GNetGraph()
            ns = openwimesh.gnetgraph.nodes()
            edg = openwimesh.gnetgraph.edges()
            time_stamp = openwimesh.gnetgraph.get_time_stamp()
            dcid = {}
            c = -1
            colors = ["red","blue","green","purple","yellow","brown","pink","orange"]
            for n in ns:
                gnetg.add_node(n[0],n[1]['ip'],n[1]['cid'])
                if n[1]['cid'] not in dcid.keys():
                    dcid[n[1]['cid']] = []
                    c = n[1]['cid']
                    dcid[n[1]['cid']].append(n[0])
                else:
                    dcid[n[1]['cid']].append(n[0])


            for ed in edg:
                gnetg.add_edge(ed[0], ed[1],weight=NetGraph.DEFAULT_WEIGHT, wired=True)

            if gnetg:
                #print id(gnetg)
                if openwimesh.gshow_graph_time_stamp < time_stamp:
                    plt.clf() # clear old image
                    plt.title(title) # reinsert title

                    if openwimesh.gshow_graph_node_count != gnetg.number_of_nodes():
                        log.debug("Show Global Graph:  Calc New Layout")
                        # generate new layout for graph
                        openwimesh.gshow_layout = layout(gnetg)
                        openwimesh.gshow_graph_node_count = gnetg.number_of_nodes()

                    log.debug("Show Global Graph:  New Time Stamp: " + str(time_stamp))
                    openwimesh.gshow_graph_time_stamp = time_stamp 
                    # draw nodes
                    for c,l in dcid.items():
                        color = colors.pop()
                        #color = random.choice(colors)
                        draw_networkx_nodes(gnetg,openwimesh.gshow_layout,nodelist=l,node_size=1500,node_color=color)
                        #colors.pop(colors.index(color))
                    # draw edges
                    draw_networkx_edges(gnetg,openwimesh.gshow_layout)
                    # getting node labels
                    labels = dict([(node,node_attributes[node_attr]) for
                        node,node_attributes in gnetg.nodes(data=True)])
                    # draw node labels
                    draw_networkx_labels(gnetg,openwimesh.gshow_layout,labels=labels)
                    # getting edges labels
                    labels=dict([((source,target), edges_attributes[attr]) for
                        source,target,edges_attributes in
                        gnetg.edges(data=True)])
                    # draw edges labels
                    draw_networkx_edge_labels(gnetg,openwimesh.gshow_layout,
                            edge_labels=labels,label_pos=0.18)

        openwimesh.gshow_ani = animation.FuncAnimation(figure, update_image,
                blit=False, interval=10000)
        plt.title(title) # insert title
        plt.show()

    @classmethod
    def list_connected(cls):
        if not openwimesh.netgraph:
            return
        log.debug("Nos conectados:")
        g = openwimesh.netgraph
        for n in g.nodes():
            if g.node[n]['conn'] is not None and not g.node[n]['conn'].disconnected:
                log.debug("  %s -> %s" % (n, g.node[n]['ip']))


    def __init__ (self, ofmac, ofip, cid, priority, algorithm, gcid, ofglobalhw, ofglobalip, uri, crossdomain, monit):
        

        # MONITORING FILES
        #f_flu = open("/home/openwimesh/dumpfluxos.txt", "w")
        #f_flu.write("Experiment,Switch,SRC_IP,DST_IP,SRC_PORT,DST_PORT,Packet_Count,Byte_Count,Duration_Sec,Duration_Nsec,Delta_Packet_Count,Delta_Byte_Count,Delta_Duration_Sec,Delta_Duration_Nsec\n")
        #f_flu.flush()
        
        self.f_latencia = open("/home/openwimesh/latencia/%s-16n-%s-lat" % (monit, ofip), "w")
        self.f_conv = open("/home/openwimesh/tempo-converg/%s-n16-%s-conv" % (monit, ofip), "w")
        openwimesh.f_lat = self.f_latencia
        openwimesh.f_conv = self.f_conv

        self.listenTo(core.openflow)

        # create the graph
        self.net_graph = NetGraph()
        #self.gnet_graph = GNetGraph()
        openwimesh.netgraph = self.net_graph

        # array of directly connected nodes, each element
        # of the array is the datapath-id of the node
        self.directly_connected_nodes = []
        openwimesh.directlyconnectednodes = self.directly_connected_nodes

        self.global_ofctl_uri = uri
        openwimesh.globalofctluri = self.global_ofctl_uri
        self.gnet_graph = Pyro4.Proxy(self.global_ofctl_uri)         # get a Pyro proxy to the greeting object
        openwimesh.gnetgraph = self.gnet_graph
        #print(self.gnet_graph.get_fortune("bahia"))
        self.async_gnetgraph=Pyro4.async(self.gnet_graph)


        # The first node of the graph is the own global controller
        
        self.net_graph.add_global_ofctl(gcid, ofglobalhw, ofglobalip)



        self.net_graph.add_ofctl(cid, ofmac, ofip)
        self.net_graph.update_ofctl_list(cid, ofmac, ofip, priority)

        #th = Thread(target=self._async_call, args=(self.async_gnetgraph.get_fortune("BBMP"),))
        #th.start()

        try:
            if gcid != cid:
                self.net_graph.add_route_ins(ofglobalip, ofmac, crossdomain)#destino global_app
                #self.net_graph.add_route_ins('192.168.199.2', '00:00:00:aa:00:03','00:00:00:aa:00:02',1)
                #self.net_graph.add_route_ins('192.168.199.3', '00:00:00:aa:00:03','00:00:00:aa:00:02',1)
            else:
                self.gnet_graph.set_gcid(gcid)
                self.gnet_graph.check_ofctl_conn()
                #self.net_graph.add_route_ins('192.168.199.252', '00:00:00:aa:00:02','00:00:00:aa:00:03',1)
        except Exception as e:
            print "erro add_route_ins: %s" % e
        

        # dictionary of nodes trying to connect to the controller,
        # in the form:
        #    connecting_nodes[MAC] = IP
        self.connecting_nodes = {}

        # list of arp-request replied in a short period of time, to avoid
        # repling duplicated requests
        self.replied_arp_req = {}

        # access control list
        self.acl = ACL()

        # keep track of installed paths (i.e. openflow rules along the graph for a
        # given application)
        #self.ph = PathHandler()

        # startup time
        self.startup_time = time.time()
        openwimesh.startuptime = self.startup_time
        openwimesh.f_conv.write("####OPENWIMESH CTRL STARTUP TIME####  \n%f\n" % (openwimesh.startuptime))
        openwimesh.f_conv.write("MAC,TIMESTAMP,CONVERGENCE_DELAY\n")
        openwimesh.f_conv.flush()

        #Quantidades de sw que este controlador pode gerenciar
        self.max_sw_capacity = 3
        
	    # topology update initial event counter
        self.ini_topology_up_count = 0
        
        # thread counting variable
        self.thread_count = 0
        
        # variable used to track a bug. TEMPORARY!!!
        self.not_in_graph = []
        # variavel armengue para fingir que è outro controlador
        self.fake_sw = {}

        self.drop_fake = {}
        openwimesh.dropfake = self.drop_fake
        openwimesh.fakesw = self.fake_sw
        
        # Set the weigth selection algorithm
        self.net_graph.set_ofctl_weight_selection_algorithm(algorithm)

    def get_startup_time(self):
        return self.startup_time

    def _async_call(self, param):
        time.sleep(20)
        print "param = %s" % param.value


    #########################################################
    # Drop the specific packet from informed event
    #
    #########################################################
    def _drop (self, event, idle_timeout=5, hard_timeout=15):
        packet = event.parsed
        sw = self.net_graph.get_by_attr('dpid', dpidToStr(event.dpid))

        # installing flow entry in sw table
        log.debug("Installing flow to drop packet from %s", dpidToStr(event.dpid))
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.idle_timeout = idle_timeout # delete entry without traffic after 5s
        msg.hard_timeout = hard_timeout # delete entry in 15s
        msg.buffer_id = event.ofp.buffer_id
        try:
            self.net_graph.node[sw]['conn'].send(msg)
        except:
            log.debug("Error installing entry in %s for packet from %s",
                    sw, dpidToStr(event.dpid))    


    #########################################################
    # Drop all packets with the same dl_dst (destination mac) from event
    #
    #########################################################
    def _drop_all (self, event, idle_timeout=5, hard_timeout=15):
        packet = event.parsed
        sw = self.net_graph.get_by_attr('dpid', dpidToStr(event.dpid))

        # installing flow entry in sw table
        log.debug("Installing flow to drop ALL packets received by %s, but destined to %s", dpidToStr(event.dpid), packet.dst)
        msg = of.ofp_flow_mod()
        msg.match.dl_dst = packet.dst
        msg.actions.append(of.ofp_action_output(port=of.OFPP_NONE))
        msg.idle_timeout = idle_timeout # delete entry without traffic after 5s
        msg.hard_timeout = hard_timeout # delete entry in 15s
        try:
            self.net_graph.node[sw]['conn'].send(msg)
        except:
            log.debug("Error installing entry in %s for packet from %s",
                    sw, dpidToStr(event.dpid))    

    #########################################################
    # _get_connecting_node_by_ip (ipaddr)
    #   - ipaddr: ip address of the node who is connecting
    #
    # This function searches in connecting_nodes list for a
    # node with ip address 'ipaddr' and returns the ethernet
    # address of that node. If the node isn't found, it returns
    # None.
    #########################################################
    def _get_connecting_node_by_ip(self, ipaddr):
        if type(ipaddr) is not str:
            ipaddr = str(ipaddr)
        for k,v in self.connecting_nodes.iteritems():
            if v == ipaddr:
                return k
        return None

    #########################################################
    # _get_out_port(node, in_port, dl_dst)
    #
    # This function returns the output port in 'node' (MAC), which
    # should be used to forward a packet coming in 'in_port' to 'dl_dst'.
    #
    #########################################################
    def _get_out_port(self, node, in_port, dl_dst):
        if type(node) is not str:
            node = str(node)
        if type(dl_dst) is not str:
            dl_dst = str(dl_dst)
        
        # define the output port
        if dl_dst == node:
            return [of.OFPP_LOCAL]
        else:
            out_port = self.net_graph.get_out_port_no(node, dl_dst)
            if out_port is None or in_port is None: 
                # we dont known how to forward, so send to all ports
                return [of.OFPP_IN_PORT, of.OFPP_ALL]
            elif out_port == in_port:
                return [of.OFPP_IN_PORT]
            else:
                return [out_port]

    # ARP-Reply: target_ip is at target_sw.mac
    def _send_arp_reply(self, target_sw, target_ip, in_port, requester_ip,
            requester_hw):
        sw = self.net_graph.node[target_sw]
        # create the arp packet
        r = packet.arp()
        r.opcode = packet.arp.REPLY
        r.hwsrc = EthAddr(target_sw)

        if type(target_ip) is str:
            target_ip = IPAddr(target_ip)
        r.protosrc = target_ip

        if type(requester_ip) is str:
            requester_ip = IPAddr(requester_ip)
        r.protodst = requester_ip

        if type(requester_hw) is str:
            requester_hw = EthAddr(requester_hw)
        r.hwdst = requester_hw

        # create the ethernet packet
        e = packet.ethernet()
        e.type = packet.ethernet.ARP_TYPE
        e.src = r.hwsrc
        e.dst = r.hwdst
        e.payload = r

        # now we send the packet back to arp requestor
        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
        msg.in_port = in_port
        conn = sw.get('conn', None)
        if conn:
            conn.send(msg)
            log.debug("Sending ARP-Reply [%s -> %s]: %s is at %s", e.src,
                    e.dst, r.protosrc, r.hwsrc)

    #########################################################
    # _install_flow_entry (switch, match_fields, actions)
    #
    # - sw_id: Identifier of the openflow switch (MAC) where the role
    #      will be installed in.
    # - match_fields: a dictionary of the fields to match.
    #      Example: {
    #           'nw_dst' : '1.1.1.2',
    #           'nw_dst' : '2.1.3.1',
    #           'nw_proto' : '6',       # TCP
    #           'tp_dst' : '6633' }
    # - actions: a ordered list of actions
    #     Example: [
    #           ['set_dl_dst', '00:00:00:00:00:01'],
    #           ['output', '1']         # output port
    #       ]
    #########################################################
    def _install_flow_entry(self, sw_id, match_fields, actions, buffer_id = None,hard_timeout=0):
        status_code = True
        status_msg  = ""
        msg = of.ofp_flow_mod()

        try:
            msg.match = of.ofp_match(**match_fields)
        except TypeError as e:
            status_msg += "Invalid match field:" + str(e) + "\n"
            status_code = False
        except:
            status_msg += "Unexpected error: " + sys.exc_info()[0]
            status_code = False

        for action in actions:
            (k, v) = action
            if k.startswith('output'):
                msg.actions.append(of.ofp_action_output(port = v))
            elif k == 'set_vlan_vid':
                msg.actions.append(of.ofp_action_output(vlan_vid = v))
            elif k == 'set_dl_src':
                msg.actions.append(of.ofp_action_dl_addr.set_src(dl_addr = v))
            elif k == 'set_dl_dst':
                msg.actions.append(of.ofp_action_dl_addr.set_dst(dl_addr = v))
            elif k == 'set_nw_src':
                msg.actions.append(of.ofp_action_nw_addr.set_src(nw_addr = v))
            elif k == 'set_nw_dst':
                msg.actions.append(of.ofp_action_nw_addr.set_dst(nw_addr = v))
            elif k == 'set_tp_src':
                msg.actions.append(of.ofp_action_tp_port.set_src(tp_port = v))
            elif k == 'set_tp_dst':
                msg.actions.append(of.ofp_action_tp_port.set_dst(tp_port = v))
            else:
                status_msg += "Unknow action: " + k + "\n"
                status_code = False

        if not status_code:
            return (status_code, status_msg)

        # TODO: how many time this role will be valid?
        # For now, it will be forever
        msg.idle_timeout = 20
        msg.hard_timeout = hard_timeout

        switch = self.net_graph.node.get(sw_id, None)
        if switch is None:
            return (False, "Invalid switch " + sw_id)

        if buffer_id:
            msg.buffer_id = buffer_id

        try:
            conn = switch['conn']
            conn.send(msg)
        except Exception as e:
            print e
            return (False, "Unexpected error: " + str(e))

        return (True, "")


    def _install_path(self, event, src_ip, dst_ip, match_fields, fwd_buffered_pkt = False):
        log.debug("_install_path called")
        #log.debug("Current installed paths:\n%s", self.ph.show())

        # recv_node_hw: host who generated the packetin to controller
        dpid = dpidToStr(event.dpid)
        recv_node_hw = self.net_graph.get_by_attr('dpid', dpid)
        if not recv_node_hw:
            log.debug("DROP packet: unknown switch %s sending packet-in", dpid)
            self._drop(event)
            return

        recv_node_ip = self.net_graph.get_node_ip(recv_node_hw)

        dst_node_hw = self.net_graph.get_by_attr('ip', dst_ip)

        if not dst_node_hw:
            dst_node_hw = self._get_crossdomain(recv_node_ip,dst_ip)

        path = self.net_graph.path(src_ip, dst_ip)
        #print (self.gnet_graph.path(src_ip,dst_ip))
        #th = Thread(target=self._async_call, args=( self.async_gnetgraph.path( src_ip,dst_ip ), ) )
        #th.start()
        print "Installing path %s -> %s -> %s. Match: %s" % (src_ip, path,
                            dst_ip, match_fields)
        log.debug("Installing path %s -> %s -> %s. Match: %s" % (src_ip, path,
            dst_ip, match_fields))
        if len(path) == 0:

            log.debug("Dropping empty path from %s to %s", src_ip, dst_ip)
            self._drop(event)
            return

        # Sanity check: a disconnected or unknown node cannot be in the middle
        # of the path, because it will not forward traffic as we expect. It is
        # only allowed to be on the begin or end of the path (actually it is
        # connecting)
        for sw in path[1:-1]:
            if self.net_graph.node[sw].get('conn', None) is None or \
                    self.net_graph.node[sw]['conn'].disconnected:
                log.debug("WARNING: Path contains a non-connected node %s. "
                        "Dropping path." % (sw))
                self._drop(event)
                #print "deu merda"
                return

        #log.debug("Edges: %s", str(self.net_graph.edges(data=True)))
        #log.debug("Graph: %s", str(self.net_graph.nodes(data=True)))

        #self.ph.add(match_fields, path)
        
        for i,sw in enumerate(path):
        #for i in range(len(path)-1, -1, -1):
            #sw = path[i]
            new_src_hw = sw
            buffer_id = None

            # the node must have a connection to the controller if we want to
            # install a path
            try:
                if not self.net_graph.node[sw].get('conn', None):
                    log.debug("WARNING: install_path - ignoring switch %s", sw)
                    continue
                
            except Exception:
                log.debug("WARNING: install_path - ignoring switch %s", sw)
                continue


            if i + 1 == len(path): # sw.next == NULL
                new_dst_hw = path[i]
            else:
                new_dst_hw = path[i+1]

            # define the input port
            if i == 0: # sw.prev == NULL
                in_port = event.port
                if fwd_buffered_pkt:
                    buffer_id = event.ofp.buffer_id
            else:
                prev_sw = path[i-1]
                in_port = self.net_graph.node[sw]['fdb'].get(prev_sw, None)

            porta_destino = None
            try:
                #print "valendo"
                if str(match_fields['tp_dst']) and str(match_fields['tp_dst']) == "6633":
                    porta_destino = "6633"
                    if porta_destino:
                        print "funcionou?"
            except Exception, e:
                log.debug("WARNING:  %s", e)

            try:
                if str(match_fields['tp_src']) and str(match_fields['tp_src']) == "6633":
                    porta_destino = "6633"
                    if porta_destino:
                        print "funcionou?"
            except Exception, e:
                log.debug("WARNING:  %s", e)
                
            # armengue para adicionar um novo sw
            ofctl_hw_addr = self.net_graph.get_hw_ofctl()
            #print "%s in %s is %s" % (dst_ip,self.fake_sw,(dst_ip in self.fake_sw))
            #print "%s in %s is %s" % (match_fields['nw_src'],self.fake_sw,(match_fields['nw_src'] in self.fake_sw))
       
            if dst_ip in self.fake_sw and porta_destino and i +2 == len(path):
                print "passei 1"
                actions = [['set_nw_src',self.fake_sw[dst_ip]], ['set_dl_src', new_src_hw], ['set_dl_dst', new_dst_hw]]
            elif match_fields['nw_src'] in self.fake_sw and porta_destino and i + 1 == len(path):
                print "passei 2"
                actions = [['set_nw_dst',dst_ip], ['set_dl_src', new_src_hw], ['set_dl_dst', new_dst_hw]]
            else:
                print "passei 3"
                actions = [['set_dl_src', new_src_hw], ['set_dl_dst', new_dst_hw]]

            log.debug("Actions: %s" % actions)
            # set the output port
            out_port = self._get_out_port(sw, in_port, new_dst_hw)
            print "a porta de entrada é %s" % in_port
            print "a porta de saida é %s" % out_port
            for i,p in enumerate(out_port):
                actions.append(['output'+str(i), p])

            # set an match field in order to avoid receive packets that are not
            # destinated to the node (e.g. in nodes that operates in
            # promiscouos mode)
            if in_port != of.OFPP_LOCAL:
                match_fields['dl_dst'] = EthAddr(new_src_hw)
            #MAIS ARMENGUE
            if dst_ip in self.fake_sw and porta_destino :
                (status, msg) = self._install_flow_entry(sw, match_fields, actions, buffer_id)
            else:
                (status, msg) = self._install_flow_entry(sw, match_fields, actions, buffer_id)
            if not status:
                log.debug("Error installing flow in %s: %s", sw, msg)
            #print "path instalado"

    def _send_to_global(self, event):
        print "oi"

    def _get_crossdomain(self,recv_node_ip,dst_node_ip):
        log.debug("Asking global_app who is %s ",dst_node_ip)
        dst_node_hw = self.net_graph.get_my_crossdomain_sw(dst_node_ip)
        if not dst_node_hw:
            crossd = self.gnet_graph.get_crossdomain(recv_node_ip,dst_node_ip,self.net_graph.get_cid_ofctl())
            if crossd is not None:
                log.debug("Add crossdomain with destination %s between %s and %s",dst_node_ip ,crossd['my_sw'],crossd['dst_sw'])
                self.net_graph.add_route_ins(dst_node_ip,crossd['my_sw'],crossd['dst_sw'])
                dst_node_hw = crossd['my_sw']
            else:
                log.debug("%s not found at global graph", dst_node_ip)
                return None

        return dst_node_hw

    def _async_add_edge_tmp(self,node1,node2):
        self.gnet_graph.add_edge(node1, node2,
                    weight=10*NetGraph.DEFAULT_WEIGHT)
        self.gnet_graph.add_edge(node2, node1,
                    weight=10*NetGraph.DEFAULT_WEIGHT, confirmed=False)

    def _handle_arp_req(self, event, arp_pkt):
        orig_src_hw = str(arp_pkt.hwsrc)
        orig_src_ip = str(arp_pkt.protosrc)
        dst_node_ip = str(arp_pkt.protodst)

        try:
            #print "%s in %s is %s" % (orig_src_ip,self.drop_fake, (orig_src_ip in self.drop_fake) ) 
            if orig_src_ip in self.drop_fake and dst_node_ip == self.drop_fake[orig_src_ip][0]:
                
                print "%s" % (time.time() - self.drop_fake[orig_src_ip][1])
                if time.time() - self.drop_fake[orig_src_ip][1] < 180:
                    print "drop fake"
                    self._drop(event)
                    return
                else:
                    del self.drop_fake[str(ether_pkt.src)]
        except Exception as e:
            log.debug("Error drop fake: %s " % e)

        # recv_node_hw: host who generated the packetin to controller
        dpid = dpidToStr(event.dpid)
        recv_node_hw = self.net_graph.get_by_attr('dpid', dpid)
        print "pkt-in gerado por %s" % recv_node_hw
        if not recv_node_hw:
            log.debug("DROP packet: unknown switch %s sending packet-in", dpid)
            self._drop(event)
            print "matei 1"
            return

        ofctl_ip = self.net_graph.get_ip_ofctl()
        dst_node_ip_path = dst_node_ip
        if ipaddress.ip_address(unicode(dst_node_ip)) in ipaddress.ip_network(unicode('192.168.199.224/27')):
            check_arp = self.gnet_graph.check_arp_req_to_ofctl(self.net_graph.get_cid_ofctl() ,orig_src_hw,dst_node_ip)
            if check_arp != "ok" and check_arp != "fake":
                log.debug("DROP packet to ofctl: sw (%s) is %s ",orig_src_hw ,check_arp)
                self._drop(event)
                print "matei dst ofctl"
                return
            if check_arp == "fake":
                dst_node_ip_path = ofctl_ip
                self.fake_sw[orig_src_ip] = dst_node_ip
                log.debug("%s will take over control %s", dst_node_ip_path,orig_src_ip)

        recv_node_ip = self.net_graph.get_node_ip(recv_node_hw)

        dst_node_hw = self.net_graph.get_by_attr('ip', dst_node_ip)
        print "destino e %s - %s" % (dst_node_ip,dst_node_hw)

        
        if not dst_node_hw:
            #dst_node_hw = self.net_graph.get_my_crossdomain_sw(dst_node_ip)
            dst_node_hw = self._get_crossdomain(recv_node_ip,dst_node_ip)
            if not dst_node_hw:
                #if self.net_graph.get_ip_ofctl() == dst_node_ip:
                #    dst_node_hw = self.net_graph.get_hw_ofctl()
                #if not dst_node_hw:
                self._send_to_global(event)
                log.debug("DROP packet: unknown destination %s (not in the graph)", dst_node_ip)
                self._drop(event)
                self.net_graph.print_nodes(ip_key=dst_node_ip,  elapsed_time=(time.time() - self.startup_time), filename='bug2.log')
                self.not_in_graph.append(dst_node_ip)
                print "matei 2"
                return

        if self.net_graph.get_ip_ofctl() == dst_node_ip and recv_node_hw == self.net_graph.get_hw_ofctl():
            recv_node_ip = self.net_graph.get_ip_ofctl()

        # Received an ARP request from a node, then add an edge between these
        # nodes
        print "mac de origem %s" % orig_src_hw
        if orig_src_hw not in self.net_graph.nodes():
            try:
                self.net_graph.add_node(orig_src_hw, orig_src_ip)
                openwimesh.addnode_time[orig_src_hw] = time.time()
            except Exception as e:
                print "Erro ao add o node: %s" % e

            print "add o %s ao netgraph" % orig_src_ip
            
            # Debugging code ...
            #log.debug("Added new node: mac=%s - ip=%s" % (orig_src_hw, orig_src_ip))
            if orig_src_ip in self.not_in_graph:
                print "Added a node which previously was not found: mac=%s - ip=%s" % (orig_src_hw, orig_src_ip)
                log.debug("Added a node which previously was not found: mac=%s - ip=%s" % (orig_src_hw, orig_src_ip))
            node = self.net_graph.get_by_attr('ip', orig_src_ip)
            node_ip = self.net_graph.get_node_ip(node)
            if not node or not node_ip:
                log.debug("Failed adding new node: mac=%s - ip=%s" % (orig_src_hw, orig_src_ip))
            # End of debugging code!
            
        if recv_node_hw != orig_src_hw and recv_node_hw not in self.net_graph.edge[orig_src_hw]:
            # add an edge with big weight, trying to exclude this edge from any
            # path
            self.net_graph.add_edge(orig_src_hw, recv_node_hw,
                    weight=10*NetGraph.DEFAULT_WEIGHT)
            # As we have an digraph, we supose to have communication from
            # recv_node to orig_src, and add a temporary edge:
            self.net_graph.add_edge(recv_node_hw, orig_src_hw,
                    weight=10*NetGraph.DEFAULT_WEIGHT, confirmed=False)
            #add global edge
            # try:
            #     th = Thread(target=self._async_add_edge_tmp, args=(orig_src_hw, recv_node_hw,))
            #     th.start()
            # except Exception as e:
            #     log.debug("Error add edge gnet (%s)" % e)
            print "add edge"

        arp_req_msg = "who-has-%s-tell-%s" % (dst_node_ip, orig_src_ip)
        log.debug("ARP-Request received in %s [%s -> %s]: %s", dpid,
                orig_src_hw, str(arp_pkt.hwdst), arp_req_msg)

        ## ARP-Request timer
        #
        # We can receive a lot of arp-request from a new node in our switches
        # already connected. The requests can be received on a same already
        # connected switch or even in other switches. In order to handle this
        # issue, we keep a list of replied arp-requests in a period of time.
        #
        if arp_req_msg in self.replied_arp_req:
            delay = time.time() - self.replied_arp_req[arp_req_msg]['time']
            if delay < ARP_REQ_DELAY:
                print "Ignoring ARP-Request replied"
                log.debug("  -> Ignoring ARP-Request replied in %d seconds"
                        " ago by %s" % (delay,
                            self.replied_arp_req[arp_req_msg]['responser']))
                self._drop(event)
                print "matei 3"
                return

        # If this is not a connection with the controller, we just use the
        # receiving node as entry point of our network and we use that node as
        # the Ethernet first hop of the communication
       
        

        if dst_node_ip != ofctl_ip and orig_src_ip != ofctl_ip and not (orig_src_ip in self.fake_sw and dst_node_ip == self.fake_sw[orig_src_ip]):
     
            print("Replying an ARP not related to the OFCTL: %s. depois return", arp_req_msg)
            log.debug("Replying an ARP not related to the OFCTL: %s", arp_req_msg)
            self._send_arp_reply(recv_node_hw, dst_node_ip, event.port, orig_src_ip,
                orig_src_hw)
            # Update the list of replied ARP-Requests
            self.replied_arp_req[arp_req_msg] = {'responser' : dpid, 
                'time' : time.time()}
            self._drop(event)
            print "matei 4"
            return

        # check if the node is trying to talk with the controller
        if dst_node_ip_path == ofctl_ip:
            # if the node who generated the packetin to controller is itself
            # the controller, then the node is directly connected
            if recv_node_hw == self.net_graph.get_hw_ofctl():
                self.directly_connected_nodes.append(orig_src_hw)

            # Now we save some information about the node that is trying to
            # connect
            self.connecting_nodes[orig_src_hw] = orig_src_ip

        match_fields = {'dl_type' : packet.ethernet.IP_TYPE,
                'nw_src' : orig_src_ip,
                'nw_dst' : dst_node_ip,
                'nw_proto' : packet.ipv4.TCP_PROTOCOL}

        if dst_node_ip_path == ofctl_ip:
            match_fields['tp_dst'] = 6633
        elif orig_src_ip == ofctl_ip:
            match_fields['tp_src'] = 6633

        self._install_path(event, recv_node_ip, dst_node_ip_path, match_fields)

        # After installing the paths, send the arp-reply related to this arp-request
        self._send_arp_reply(recv_node_hw, dst_node_ip, event.port, orig_src_ip,
                orig_src_hw)
        print "arp-reply enviado para %s" % orig_src_ip
        
        # Update the list of replied ARP-Requests
        self.replied_arp_req[arp_req_msg] = {'responser' : dpid, 
                'time' : time.time()}

        # XXX: after setting up the path and replying the arp-request
        # we can discard the original arp-req
        log.debug("DEBUG: drop after all")
        self._drop(event)

    def _handle_tcp_udp(self, event, ip_pkt):
        nw_src = str(ip_pkt.srcip)
        nw_dst = str(ip_pkt.dstip)
        tp_src = ip_pkt.next.srcport
        tp_dst = ip_pkt.next.dstport

        # recv_node_hw: host who generated the packetin
        dpid = dpidToStr(event.dpid)
        recv_node_hw = self.net_graph.get_by_attr('dpid', dpid)
        if not recv_node_hw:
            log.debug("DROP packet: unknown switch %s sending packet-in", dpid)
            self._drop(event)
            return
        recv_node_ip = self.net_graph.get_node_ip(recv_node_hw)
        nw_dst_path = nw_dst

       

        try:
            if str(tp_dst) and str(tp_dst) == "6633" and nw_src in self.fake_sw and nw_dst == self.fake_sw[nw_src]:
                nw_dst_path = self.net_graph.get_ip_ofctl()
        except Exception as e:
            print "erro armengue para o tcp: %s" % e


        match_fields = {'dl_type' : packet.ethernet.IP_TYPE,
                'nw_src' : nw_src,
                'nw_dst' : nw_dst,
                'nw_proto' : ip_pkt.protocol,
                'tp_src' : tp_src,
                'tp_dst' : tp_dst}

        self._install_path(event, recv_node_ip, nw_dst_path, match_fields, fwd_buffered_pkt = True)

    def _handle_icmp(self, event, ip_pkt):
        nw_src = str(ip_pkt.srcip)
        nw_dst = str(ip_pkt.dstip)
        icmp_type = ip_pkt.next.type
        icmp_code = ip_pkt.next.code


        #th = Thread(target=self._async_call, args=(self.async_gnetgraph.get_fortune("BBMP"),))
        #th.start()
        # recv_node_hw: host who generated the packetin

        dpid = dpidToStr(event.dpid)

        print "################### ICMP ID: %s" % ip_pkt.next.next.id
        if nw_dst == '192.168.1.1':
            # RECEBIDO PING ECHO REQUEST de outro possível domínio global
            # 
            # ESTA MSG FOI GERADA POR UM:
            # nping --dest-mac 00:00:00:aa:00:06 --icmp --icmp-id 3 192.168.1.1 -c 2
            # nping --dest-mac <MAC_VIZINHO_FORA_DO_DOMINIO> --icmp --icmp-id <GLOBALCTRL_ID> <IP_REDE_FAKE> -c <COUNT>

            #extrair CID do ICMP ID e enviar ao GlobalCTRL, para então se decidir quem será o ÚNICO global da rede
            cid = ip_pkt.next.next.id

            #
            # TODO: send CID, DPID(MAC) and src IP to global via Pyro
            # 

        recv_node_hw = self.net_graph.get_by_attr('dpid', dpid)
        if not recv_node_hw:

            log.debug("DROP packet: unknown switch %s sending packet-in", dpid)
            self._drop(event)
            return
        recv_node_ip = self.net_graph.get_node_ip(recv_node_hw)

        nw_dst_path = nw_dst

        # try:
        #     if nw_src in self.fake_sw and nw_dst == self.fake_sw[nw_src]:
        #         nw_dst_path = self.net_graph.get_ip_ofctl()
        # except Exception as e:
        #     print "Erro armengue para icmp: %s" % e

        match_fields = {'dl_type' : packet.ethernet.IP_TYPE,
                'nw_src' : nw_src,
                'nw_dst' : nw_dst,
                'nw_proto' : ip_pkt.protocol,
                'tp_src' : icmp_type,
                'tp_dst' : icmp_code}

        self._install_path(event, recv_node_ip, nw_dst_path, match_fields, fwd_buffered_pkt = True)

    def _change_ofctl(self, sw_ip_addr):
        print "changing"
        
        ofctl_ip = self.net_graph.get_ip_ofctl()
        ofctl_hw = self.net_graph.get_hw_ofctl()
        log.debug("PARAMETROS: %s %s" % (sw_ip_addr, ofctl_ip,))
        sw_hw_addr = self.net_graph.get_by_attr('ip', sw_ip_addr)
        path = self.net_graph.path(ofctl_ip,sw_ip_addr)
        print path
        i = path.index(sw_hw_addr)
        previous_sw = path[i-1]
        previous_ip = self.net_graph.get_node_ip(previous_sw)

        now = time.time()

        os.system("bash /home/openwimesh/novo-controlador.sh 2 %s %s" % (sw_ip_addr, ofctl_ip))
        self.drop_fake[sw_ip_addr] = []
        self.drop_fake[sw_ip_addr].append(self.fake_sw[sw_ip_addr])
        
        self.drop_fake[sw_ip_addr].append(now)
        del self.fake_sw[sw_ip_addr]
        print "Fake = %s " % self.fake_sw
        #try:
        #    self.net_graph.remove_node(sw_hw_addr)
        #except Exception as e:
        #    log.debug("Error removing node (%s)" % e)
        #os.system("arp -d %s" % sw_ip_addr)
        #os.system("ovs-ofctl del-flows ofsw0 tcp,nw_dst=%s,tp_src=6633" % sw_ip_addr)
        #os.system("ovs-ofctl del-flows ofsw0 tcp,nw_src=%s,tp_dst=6633" % sw_ip_addr)
        os.system("ovs-ofctl add-flow ofsw0 idle_timeout=20,tcp,nw_src=%s,nw_dst=%s,tp_dst=6633,actions=mod_dl_src:%s,mod_dl_dst:%s,LOCAL,--monit=%s" % (sw_ip_addr,ofctl_ip,ofctl_hw,ofctl_hw, time.time()))
        match_fields = {'dl_type' : packet.ethernet.IP_TYPE,
                'nw_src' : ofctl_ip,
                'nw_dst' : sw_ip_addr,
                'nw_proto' : packet.ipv4.TCP_PROTOCOL}
        match_fields['tp_src'] = 6633

        buffer_id = None

        actions = [['set_dl_src', previous_sw], ['set_dl_dst', sw_hw_addr]]

        

        if previous_sw != ofctl_hw:
            match_fields['dl_dst'] = EthAddr(previous_sw)
            actions.append(['output'+str(0), 65528])
        else:
            actions.append(['output'+str(0), 1])
           
        (status, msg) = self._install_flow_entry(previous_sw, match_fields, actions, buffer_id)
        #os.system("ovs-ofctl add-flow ofsw0 idle_timeout=20,tcp,nw_src=%s,nw_dst=%s,tp_src=6633,actions=mod_dl_src:%s,mod_dl_dst:%s,output:1" % (ofctl_ip,sw_ip_addr,previous_sw,sw_hw_addr))

        print "fim do fake"


    
    def _async_add_edge(self,node1,node2):
        self.gnet_graph.add_edge(node1, node2,
                        weight=NetGraph.DEFAULT_WEIGHT, wired=True)
        self.gnet_graph.add_edge(node2, node1,
                        weight=NetGraph.DEFAULT_WEIGHT, wired=True)

    def _async_add_node(self,hw,ip,cid):
        self.gnet_graph.add_node(hw, ip, cid)

    

    def _handle_ConnectionUp (self, event):
        """
        Handles a switch that has established a connection to the controller
        """
        log.debug("!@# Connection UP from %02d (%s) - time from startup: %f" % (event.dpid, event.connection, time.time() - self.startup_time))
        openwimesh.f_conv.write("%s,%f,%f\n"%(event.connection, time.time(), time.time() - self.startup_time))
        openwimesh.f_conv.flush()

        sw_hw_addr = None
        sw_ip_addr = None

        ports = []
        for p in event.ofp.ports:
            if p.port_no == of.OFPP_LOCAL:
                sw_hw_addr = str(p.hw_addr)
            else:
                ports.append({'port_no' : p.port_no,
                    'hw_addr' : str(p.hw_addr),
                    'name' : p.name})

        attrs = {}
        attrs['ports'] = ports
        attrs['dpid'] = dpidToStr(event.dpid)
        attrs['conn'] = event.connection

        directly_connected = False
        if sw_hw_addr in self.directly_connected_nodes:
            directly_connected = True

        attrs['ip'] = event.connection.sock.getpeername()[0]
        # TODO: the bellow code is no more needed
        if sw_hw_addr in self.connecting_nodes:
            # once the node is now connected,
            # it should be removed from connecting list
            del self.connecting_nodes[sw_hw_addr]

        print "add node %s" % sw_hw_addr

        self.net_graph.add_node(sw_hw_addr, **attrs)
        try:
            log.debug("addnode_time = %s" % openwimesh.addnode_time)
            del openwimesh.addnode_time[sw_hw_addr]
        except Exception as e:
            log.debug("Erro dele addnode_time: %s" % e)
        ofctl_hw_addr = str(self.net_graph.get_hw_ofctl())

        attrs['cid'] = self.net_graph.get_cid_ofctl()
        try:
            
            th = Thread(target=self._async_add_node, args=(sw_hw_addr, attrs['ip'], attrs['cid'],))
            th.start()
            

            if directly_connected:
                #ofctl_hw_addr = self.net_graph.get_hw_ofctl()
                log.debug("INFO: adding edge %s <-> %s", ofctl_hw_addr, sw_hw_addr)
                self.net_graph.add_edge(ofctl_hw_addr, sw_hw_addr,
                        weight=NetGraph.DEFAULT_WEIGHT, wired=True)
                self.net_graph.add_edge(sw_hw_addr, ofctl_hw_addr,
                        weight=NetGraph.DEFAULT_WEIGHT, wired=True)
                #no grafo global
                th1 = Thread(target=self._async_add_edge, args=(ofctl_hw_addr, sw_hw_addr,))
                th1.start()

            
            print("Gnet.nodes:",self.gnet_graph.nodes())
            #print(self.gnet_graph.edges())

                
        except Exception as e:
            log.debug("Error conn up (%s)" % e)

        if sw_hw_addr == ofctl_hw_addr:
            ofctl_ip = self.net_graph.get_ip_ofctl()
            cid = self.net_graph.get_cid_ofctl()
            self.gnet_graph.add_ofctl(cid, ofctl_hw_addr, ofctl_ip)

        # if self.max_sw_capacity < self.net_graph.number_of_nodes():
        #     print "calma"
        #     th2 = Thread(target=self._make_ofctl, args=(sw_hw_addr,))
        #     th2.start()
        # else:
        #     #se for fake de controlador mudar o controlador no switch
        #     sw_ip_addr = self.net_graph.get_node_ip(sw_hw_addr)
        #     if sw_ip_addr in self.fake_sw:
        #         th3 = Thread(target=self._change_ofctl, args=(sw_ip_addr,))
        #         th3.start()
            

    def _handle_ConnectionDown (self, event):
        log.debug("Connection Down from node %s" % dpidToStr(event.dpid))
        dpid = dpidToStr(event.dpid)
        sw_mac = self.net_graph.get_by_attr('dpid', dpid)
        try:
            sw_ip = self.net_graph.get_node_ip(sw_mac)
            if sw_ip in self.fake_sw:
                self.drop_fake[sw_ip] = []
                self.drop_fake[sw_ip].append(self.fake_sw[sw_ip])
                now = time.time()
                self.drop_fake[sw_ip].append(now)
                del self.fake_sw[sw_ip]
        except Exception as e:
            log.debug("ERROR fake (%s)",e)

        if sw_mac in self.directly_connected_nodes:
            self.directly_connected_nodes.remove(sw_mac)
        try:
            self.net_graph.remove_node(sw_mac)
        except Exception as e:
            log.debug("Error removing node from graph at connDown(%s)" % e)
        try:
            th = Thread(target=self.gnet_graph.remove_node, args=(sw_mac,self.net_graph.get_cid_ofctl(),))
            th.start()
            #print("gnet remove node err: %s " % self.gnet_graph.remove_node(sw_mac,self.net_graph.get_cid_ofctl()))
        except Exception as e:
            log.debug("Error conn down node from gnetgraph (%s)" % e)

    ########################################################
    # _handle_PacketIn (event)
    #########################################################
    def _handle_PacketIn (self, event):
        """
        Handles packet in messages from some switch
        The actual code is in a function which is
        called using threads or not
        """

        self.thread_count += 1
        # Operation using threads. Use only one method!!!
        #thread.start_new_thread( handle_PacketIn_Function , (self,  event ) ) 
        # Operation without threads. Use only one method!!!
        handle_PacketIn_Function (self,  event )

    ###########################################################
    # add_node: Adiciona no ao net_graph do controlador slave 
    ###########################################################

    def _add_node (self, hwaddr, ipaddr):
        """
        """

        self.net_graph.add_node(hwaddr, ipaddr)


def _handle_EchoReply (event):
    """
    Handler to calculate latency of each node from an echo reply
    """
    log.debug("Got echo reply")

    dpid = dpidToStr(event.dpid)
    sw_mac = openwimesh.netgraph.get_by_attr('dpid', dpid)
    #print "SW_MAC = %s"%(sw_mac)
    #log.debug("DPID: %s SW_MAC = %s", dpid, sw_mac)
    if sw_mac:
        now = time.time()
        latency = now - openwimesh.netgraph.get_node_timestamp(sw_mac)

        now_date = time.strftime("%y-%m-%d %H:%M:%S",time.gmtime())
        
        openwimesh.netgraph.set_node_latency(sw_mac, latency * 1000)
        #print "!@# Rcvd Echo reply from %s: Latency= %f" %(sw_mac, openwimesh.netgraph.get_node_latency(sw_mac))
        openwimesh.f_lat.write("%s,%s,%f\n"%(sw_mac, now_date, latency * 1000))
        openwimesh.f_lat.flush()
        #print "Node latency: %f"%(openwimesh.netgraph.get_node_latency(sw_mac))
    else:
        print "Drop echo reply - MAC addr matches no node in graph"

#\TODO: Handle statistics table/port/flows

def _poller_check_conn(ofpox, interval, timeout):
    if not openwimesh.netgraph:
        return

    # "er" means Echo Request
    er = of.ofp_echo_request().pack()
    now = time.time()
    dead = []
    
    for n in openwimesh.netgraph.nodes():
        # check if the node is connected
        
        # Avoiding that a node which is connecting to the
        #controller ('conn' attribute is yet "None") be removed
        if openwimesh.netgraph.node[n]['conn'] is None:
            try:
                if now - openwimesh.addnode_time[n] > 10:
                    del openwimesh.addnode_time[n]
                    dead.append(n)
                    log.debug("Removendo no que demorou para conectar")
            except Exception as e:
                print "Error: %s" % e
                log.debug("Erro addnode_time: %s" % e)
            continue

        if openwimesh.netgraph.node[n]['conn'].disconnected: 
            dead.append(n)
            continue

        if  now - openwimesh.netgraph.node[n]['conn'].idle_time > (interval+timeout):
            dead.append(n)
            continue

        # if the node is connected, send an echo request message
        now = time.time()

        openwimesh.netgraph.set_node_timestamp(n, now)
        #print "Timestamp to %s sent" % openwimesh.netgraph.node[n]
        openwimesh.netgraph.node[n]['conn'].send(er)


    for n in dead:
        log.debug("Timeout from node %s" % n)
        try:
            sw_ip = openwimesh.netgraph.get_node_ip(n)
            if sw_ip in openwimesh.fakesw:
                openwimesh.dropfake[sw_ip] = []
                openwimesh.dropfake[sw_ip].append(openwimesh.fakesw[sw_ip])
                now = time.time()
                openwimesh.dropfake[sw_ip].append(now)
                del openwimesh.fakesw[sw_ip]
        except Exception as e:
            log.debug("ERROR fake (%s)",e)

        try:
            if n in openwimesh.directlyconnectednodes:
                openwimesh.directlyconnectednodes.remove(n)
            openwimesh.netgraph.remove_node(n)
            
        except Exception as e:
            log.debug("Error removing node from graph (%s): %s" % (n,e))

        try:
            th = Thread(target=openwimesh.gnetgraph.remove_node, args=(n,openwimesh.netgraph.get_cid_ofctl(),))
            th.start()
            #print("gn err: %s" % openwimesh.gnetgraph.remove_node(n,openwimesh.netgraph.get_cid_ofctl()))
        except Exception as e:
            log.debug("Error removing node from gnetgraph (%s)" % e)

def _poller_check_global_task(ofpox, interval, timeout):
    if not openwimesh.gnetgraph:
        return

    cid = openwimesh.netgraph.get_cid_ofctl()
    ofctl_hw = openwimesh.netgraph.get_hw_ofctl()
    ofctl_ip = openwimesh.netgraph.get_ip_ofctl()
    nodes = openwimesh.netgraph.nodes()
    openwimesh.gnetgraph.add_ofctl(cid,ofctl_hw,ofctl_ip)
    openwimesh.gnetgraph.update_nodes(cid, nodes)
    log.debug("Checking if there are tasks from global_app")
    # new_ofctl_hw = openwimesh.gnetgraph.check_creating_new_ofctl(cid)
    # #print new_ofctl_hw
    # if new_ofctl_hw:
    #     print "calma"
    #     th = Thread(target=openwimesh.make_ofctl, args=(new_ofctl_hw,))
    #     th.start()

    
def launch (ofmac, ofip, cid=0, priority=0, gcid=0, ofglobalhw=None, ofglobalip=None, uri=None, crossdomain=None, interval=5, swtout=3, algorithm=0, monit=0): # interval=5, swtout=3 were the original values
    core.openflow.miss_send_len = 1024
    core.openflow.clear_flows_on_connect = False
    try:
        core.registerNew(openwimesh, ofmac, ofip, cid, priority, algorithm, gcid, ofglobalhw, ofglobalip, uri, crossdomain, monit)
    except Exception as e:
        print "Erro no launch: %s" % e
    Timer(interval, _poller_check_conn, recurring=True, args=(core.openflow,interval,swtout,))
    Timer(interval, _poller_check_global_task, recurring=True, args=(core.openflow,interval,swtout,))
    core.openflow.addListenerByName("EchoReply", _handle_EchoReply)