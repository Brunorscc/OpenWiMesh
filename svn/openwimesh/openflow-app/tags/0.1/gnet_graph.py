from networkx import DiGraph
from networkx import shortest_path
from net_graph import NetGraph
from time import time


Mb=1024.0*1024.0



class GNetGraph(NetGraph):
    DEFAULT_WEIGHT = 600
    # timeout for confirm an edge
    CONFIRM_EDGE_TOUT = 20  #20 originally
    # timestamp of graph to verify changes
    time_stamp = None

    def __init__(self):
        DiGraph.__init__(self)
        self.ofctl_list = {}
        self.weight_selection_algorithm = None
        self.time_stamp = 0

    def add_node(self, hwaddr, ip=None, cid=None):
        
        DiGraph.add_node(self, hwaddr, ip=ip, cid=cid, name=hwaddr[12:])
        # update time stamp
        self.time_stamp += 1

    def get_node_cid(self, hwaddr):
        node = self.node[hwaddr]
        if node:
            return node['cid']
        else:
            return None

    def update_ofctl_list(self, cid, hwaddr, ipaddr, priority=1000,last_update=time()):
        self.ofctl_list[cid]= {'hwaddr': hwaddr, 'ipaddr': ipaddr, 'priority': priority, 'last_update': last_update}

    def remove_ofctl(self,cid):
        if cid in self.ofctl_list:
            del self.ofctl_list[cid]
        return

    def get_fortune(self, name):
        return "Hello, {0}. Here is your fortune message:\n" \
               "Tomorrow's lucky number is 12345678.".format(name)

    def remove_node(self, n):
        if n not in self.nodes():
            return
        DiGraph.remove_node(self, n)

    def get_hw_in_ofctl_list(self,ofctl_ip):
        for cid in self.ofctl_list:
            if self.ofctl_list[cid]['ipaddr'] == ofctl_ip:
                return self.ofctl_list[cid]['hwaddr']
        return None

    def get_by_attr(self, attr, value):
        for node in self.nodes(data=True):# porque data=True?
            if node[1].get(attr, None) == value:
                return node[0]
        return None

    def check_by_attr_cid(self):
        nodes = []
        for node in self.nodes(data=True):# porque data=True?
            if not node[1].get('cid', None):
                nodes.append(node[0])
        return nodes

    def get_node_list_by_attr(self, attr, value):
        node_list = []
        for node in self.nodes(data=True):# porque data=True?
            if node[1].get(attr, None) == value:
                node_list.append(node[0])
        return node_list

    def get_node_list_by_path_len(self,nodes,cid,thold=3):
        nl = []
        dst_mac = self.ofctl_list[cid]['hwaddr']
        for node in nodes:
            try:
                if len(shortest_path(self, node, dst_mac, 'weight')) > thold:
                    nl.append(node)
            except:
                continue

        return nl

    def add_edge(self, source_mac, target_mac, signal=None,
            traffic_byt=None, speed_mbps=None, d_speed_mbps=None,
            residual_bw=None, weight=None, confirmed=True, wired=False):
        if weight is None:
            weight = self.DEFAULT_WEIGHT
        DiGraph.add_edge(self, source_mac, target_mac, signal=signal,
                traffic_byt=traffic_byt, speed_mbps=speed_mbps,
                d_speed_mbps=d_speed_mbps, weight=weight, confirmed=confirmed,
                residual_bw=residual_bw, last_update=time(), wired=wired)
        # update time stamp
        self.time_stamp += 1

    def get_node_edges_update_state(self, node, attr='signal'):
        for edge in self.edges(data=True):
            if edge[1] == node and edge[2].get(attr, None) != None:
                return True
        return False

    def path(self, src_ip, dst_ip):
        src_mac = self.get_by_attr('ip', src_ip)
        dst_mac = self.get_by_attr('ip', dst_ip)

        if src_mac is None:
            src_mac = self.get_hw_in_ofctl_list(src_ip)
            if src_mac is None:
                return []
        if dst_mac is None:
            dst_mac = self.get_hw_in_ofctl_list(dst_ip)
            if dst_mac is None:
                return []

        try:
            return shortest_path(self, src_mac, dst_mac, 'weight')
        except Exception as e:
            return e

    def update_edges_of_node(self, node, assoc_list):
        if node not in self.nodes():
            return False

        # update the neighbors of node with info from graphClient()
        for t in assoc_list:
            iface, neigh, signal, speed_mbps, traffic_byt, d_speed_mbps = (
                    t[0], t[1], int(t[2]), float(t[3]), int(t[4]), float(t[5]))
            

            # we only update graph info for connected nodes, because
            # if we add an unknown node to the graph, it may be required
            # by some path but we cannot configure this node and, in this way,
            # our path will be broken
            if neigh not in self.nodes():
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
        del_nodes = []
        for n in self.edge[node]:
            wired = self.edge[node][n]['wired']
            delay = time() - self.edge[node][n]['last_update']
            if not wired and delay > self.CONFIRM_EDGE_TOUT:
                del_nodes.append(n)
        for n in del_nodes:
            self.remove_edge(node, n)
        # update time stamp
        self.time_stamp += 1
