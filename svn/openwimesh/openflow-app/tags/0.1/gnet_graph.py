from net_graph import NetGraph
from time import time

class GNetGraph(NetGraph):

    def __init__(self):
        DiGraph.__init__(self)
        self.time_stamp = 0

    def add_node(self, hwaddr, ip=None, dpid=None, conn=None, ports=None,
            fdb=None, cid=None):
        if ports is None:
            ports = []
        if fdb is None:
            fdb = {}
        DiGraph.add_node(self, hwaddr, ip=ip, dpid=dpid, conn=conn,
                    ports=ports, fdb=fdb, cid=cid, name=hwaddr[12:])
        # update time stamp
        self.time_stamp += 1