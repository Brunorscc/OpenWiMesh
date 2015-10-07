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

from networkx import DiGraph
from networkx import shortest_path
from time import time
from controller import Controller


Mb=1024.0*1024.0


class NetGraph(DiGraph, Controller, object):
    # default weight - greater than any possible residual bw
    DEFAULT_WEIGHT = 600
    # timeout for confirm an edge
    CONFIRM_EDGE_TOUT = 20  #20 originally
    # timestamp of graph to verify changes
    time_stamp = None

    def __init__(self):
        DiGraph.__init__(self)

        self.ofctl_list = []
        self.route_ins_table = {}
        self.weight_selection_algorithm = None
        # init time stamp
        self.time_stamp = 0

    def add_route_ins(self, dst_addr, crossd_hw, dst_sw, crossd_out_port):
        self.route_ins_table[dst_addr] = {'crossd_hw': crossd_hw, 'dst_sw': dst_sw, 'crossd_out_port': crossd_out_port }

    def get_crossd_by_attr(self, attr, value):
        for dst_addr in self.route_ins_table:
            if self.route_ins_table[dst_addr][attr] == value:
                return dst_addr
        return None

    def get_crossdomain_sw(self,dst_addr):
        if dst_addr not in self.route_ins_table:
            return None
        return self.route_ins_table[dst_addr]['crossd_hw']

    def get_crossdomain_dst_sw(self,dst_addr):
        if dst_addr not in self.route_ins_table:
            return None
        return self.route_ins_table[dst_addr]['dst_sw']       

    def get_crossdomain_out_port(self,dst_addr):
        if dst_addr not in self.route_ins_table:
            return None
        return self.route_ins_table[dst_addr]['crossd_out_port'] 

    def update_ofctl_list(self, cid, hwaddr, ipaddr, priority):
        l = [cid, hwaddr, ipaddr, priority]
        self.ofctl_list.append(l)

    def print_ofctl_list(self):
        print sorted( self.ofctl_list, key=lambda l: l[3])

    def add_node(self, hwaddr, ip=None, dpid=None, conn=None, ports=None,
            fdb=None):
        if ports is None:
            ports = []
        if fdb is None:
            fdb = {}
        DiGraph.add_node(self, hwaddr, ip=ip, dpid=dpid, conn=conn,
                ports=ports, fdb=fdb, name=hwaddr[12:])
        # update time stamp
        self.time_stamp += 1

    def remove_node(self, n):
        if n not in self.nodes():
            return
        if self.node[n]['conn'] is not None \
                    and not self.node[n]['conn'].disconnected:
            self.node[n]['conn'].disconnect()
        DiGraph.remove_node(self, n)
        #log.debug("Node with hwaddr \"%s\"removed" % hwaddr)
    def set_ofctl_weight_selection_algorithm(self, algorithm):
        self.weight_selection_algorithm = int(algorithm)

    def get_by_attr(self, attr, value):
        for node in self.nodes(data=True):# porque data=True?
            if node[1].get(attr, None) == value:
                return node[0]
        return None

    def get_node_edges_update_state(self, node, attr='signal'):
        for edge in self.edges(data=True):
            if edge[1] == node and edge[2].get(attr, None) != None:
                return True
        return False

    # Print the node detail using the opened file handle and the informed node object
    def print_node_detail(self, node, file):
        file.write('  --> hwaddr: .' + node[0]       + '.\n')
        file.write('      ip:     .' + node[1]['ip'] + '.\n')
        file.write('      dpid:   .' + ('None' if node[1]['dpid'] is None else node[1]['dpid']) + '.\n')
        file.write('      conn:   .' + ('None' if node[1]['conn'] is None else 'Connected')     + '.\n')

    # Print the node based on the ip-key or mac-key or all nodes if no key is informed
    def print_nodes(self, mac_key=None,  ip_key=None, elapsed_time = 0,  filename = 'bug.log',  info=None):
        f = open(filename, 'a')
        elaptime = "%.1f" % elapsed_time
        f.write('Elapsed time:%s, ip key used:.%s., mac key used:.%s., info:.%s.\n' % (elaptime,  ip_key ,  mac_key ,  info) )
        if ip_key is not None:
            found = False
            for node in self.nodes(data=True):
                if ip_key == node[1]['ip']:
                    self.print_node_detail(node,  f)
                    found = True
            if not found:
                f.write('Node not found on graph based on IP: .%s.\n' %  ip_key)
        elif mac_key is not None:
            found = False
            for node in self.nodes(data=True):
                if mac_key == node[0]:
                    self.print_node_detail(node,  f)
                    found = True
            if not found:
                f.write('Node not found on graph based on MAC: .%s.\n' %  ip_mac)
        else:
            for node in self.nodes(data=True):
                self.print_node_detail(node,  f)
        f.close
        return 



    def get_node_ip(self, hwaddr):
        node = self.node[hwaddr]
        if node:
            return node['ip']
        else:
            return None

    def set_node_ip(self, hwaddr, ip):
        node = self.node[hwaddr]
        if node:
            node['ip'] = ip
    def get_out_port_no(self, node, dl_dst):
        if node not in self.nodes():
            return None
        if dl_dst in self.node[node]['fdb']:
            return self.node[node]['fdb'][dl_dst]
        else:
            return None

    def convert_port_name_to_no(self, node, port_name):
        if node not in self.nodes():
            return None
        for d in self.node[node]['ports']:
            if d['name'] == port_name:
                return d['port_no']
        return None

    def path(self, src_ip, dst_ip):
        src_mac = self.get_by_attr('ip', src_ip)
        dst_mac = self.get_by_attr('ip', dst_ip)
        print "src_mac = %s dst_mac = %s" % (src_mac, dst_mac)
        ofctl_ip = self.get_ip_ofctl()
        if src_mac is None:
            if ofctl_ip == src_ip:
                src_mac = self.get_hw_ofctl()
            else:
                return []
        if dst_mac is None:
            if ofctl_ip == dst_ip:
                dst_mac = self.get_hw_ofctl()
            else:
                dst_mac = self.get_crossdomain_sw(dst_ip)
                if dst_mac is not None:
                    domain_path = shortest_path(self, src_mac, dst_mac, 'weight')
                    if len(domain_path) != 0:
                        dst_sw = self.get_crossdomain_dst_sw(dst_ip)
                        domain_path.append(dst_sw)
                    return domain_path
                else:
                    return []

        return shortest_path(self, src_mac, dst_mac, 'weight')

    def add_edge(self, source_mac, target_mac, signal=None,
            traffic_byt=None, speed_mbps=None, d_speed_mbps=None,
            residual_bw=None, weight=None, confirmed=True, wired=False):
        if weight is None:
            weight = self.DEFAULT_WEIGHT

        print "wired is %s" % wired
        DiGraph.add_edge(self, source_mac, target_mac, signal=signal,
                traffic_byt=traffic_byt, speed_mbps=speed_mbps,
                d_speed_mbps=d_speed_mbps, weight=weight, confirmed=confirmed,
                residual_bw=residual_bw, last_update=time(), wired=wired)
        # update time stamp
        self.time_stamp += 1

    # update_edges_of_node
    #  - node: the identifier of the node who collected the association info
    #  - assoc_list: a list of tuples containing the following information on
    #    each tuple:
    #       (IFACE, NEIGH, SIGNAL, TRAFFIC, SPEED, D_SPEED), where:
    #       IFACE - the iface used on 'node' to connect do NEIGH
    #       NEIGH - the identifier (MAC Addr) of the neighbor
    #       SIGNAL - level of signal in the wifi communication
    #       TRAFFIC - sum of tx and rx traffic on IFACE
    #       SPEED - the speed in which the interface is working
    #       D_SPEED - our derivation speed from SINR
    # 
    def update_edges_of_node(self, node, assoc_list):
        if node not in self.nodes():
            return False



        # update the neighbors of node with info from graphClient()
        for t in assoc_list:
            iface, neigh, signal, speed_mbps, traffic_byt, d_speed_mbps = (
                    t[0], t[1], int(t[2]), float(t[3]), int(t[4]), float(t[5]))
            
            port_no = self.convert_port_name_to_no(node, iface)
            if port_no is not None:
                self.node[node]['fdb'][neigh] = port_no

            # we only update graph info for connected nodes, because
            # if we add an unknown node to the graph, it may be required
            # by some path but we cannot configure this node and, in this way,
            # our path will be broken
            if neigh not in self.nodes() or self.node[neigh]['conn'] is None \
                    or self.node[neigh]['conn'].disconnected:
                #print "neigh is %s" % neigh
                continue

            residual_bw = d_speed_mbps
            if node in self.edge[neigh]:
                last_update = self.edge[neigh][node]['last_update']
                last_traffic_byt = self.edge[neigh][node]['traffic_byt'] or 0

                delta_time = time() - last_update
                delta_byt = traffic_byt - last_traffic_byt
                in_use_mbps = (delta_byt*8.0/Mb) / delta_time
                
                residual_bw = d_speed_mbps - in_use_mbps
                # the in_use_mbps is the same for all neighbors, but the speed
                # may not be. In the case the speed_mbps is different between two
                # nodes, the residual_bw could be negative. This situation
                # actually means that the residual_bw is zero (all the bw is in
                # use)
                if residual_bw < 0:
                    residual_bw = 0

            if self.weight_selection_algorithm == 1: # HLRB: Highest Link Residual Bandwidth
                weight = round(self.DEFAULT_WEIGHT / float(1 + residual_bw), 2)
            elif self.weight_selection_algorithm == 2: # HLRB-SHC: Highest Link Residual Bandwidth in Same Hop Count
                weight = round(self.DEFAULT_WEIGHT + self.DEFAULT_WEIGHT / float(1 + residual_bw), 2)
            else: # Hop Count
                weight = self.DEFAULT_WEIGHT

            self.add_edge(neigh, node, signal, traffic_byt, speed_mbps,
                    d_speed_mbps, residual_bw, weight)

        # remove expired edges (those who were not seen by graphClient in some time)
        #log.debug("Edges: %s" % self.edges(data=True))
        print "Remover arestas"
        del_nodes = []
        #print "self.edge[node] is %s" % self.edge[node]
        for n in self.edge[node]:
            print "n is %s" % n
            wired = self.edge[node][n]['wired']
            delay = time() - self.edge[node][n]['last_update']
            print " if not %s and %s > %s " % (wired,delay, self.CONFIRM_EDGE_TOUT)
            if not wired and delay > self.CONFIRM_EDGE_TOUT:
                del_nodes.append(n)
        for n in del_nodes:
            try:
                print "ciao"
                self.remove_edge(node, n)
            except Exception as e:
                print "erro remove edge: %s" % e
        # update time stamp
        self.time_stamp += 1

