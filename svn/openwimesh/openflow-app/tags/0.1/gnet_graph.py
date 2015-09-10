from networkx import DiGraph
from networkx import shortest_path
from net_graph import NetGraph
from time import time

class GNetGraph(NetGraph):

    def __init__(self):
        DiGraph.__init__(self)
        self.weight_selection_algorithm = None
        self.time_stamp = 0

    def add_node(self, hwaddr, ip=None, cid=None):
        
        DiGraph.add_node(self, hwaddr, ip=ip, cid=cid, name=hwaddr[12:])
        # update time stamp
        self.time_stamp += 1

    def get_fortune(self, name):
        return "Hello, {0}. Here is your fortune message:\n" \
               "Tomorrow's lucky number is 12345678.".format(name)

    def remove_node(self, n):
        if n not in self.nodes():
            return
        DiGraph.remove_node(self, n)
