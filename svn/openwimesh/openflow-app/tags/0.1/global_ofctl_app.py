import Pyro4
import netifaces as ni
import time
from gnet_graph import GNetGraph
import os
import unittest



class global_ofcl_app(object):
	"""docstring for global_ofcl_app"""
	def __init__(self):
		self.gnet_graph = GNetGraph()
		self.nome = None
		self.output = None

	def get_fortune(self,name):
		return self.gnet_graph.get_fortune(name)

	@Pyro4.oneway
	def add_node(self, hwaddr, ip=None, cid=None):
		self.gnet_graph.add_node(hwaddr, ip, cid)

	@Pyro4.oneway
	def add_edge(self, source_mac, target_mac, signal=None, traffic_byt=None, speed_mbps=None, d_speed_mbps=None,residual_bw=None, weight=None, confirmed=True, wired=False):

		self.gnet_graph.add_edge(source_mac, target_mac, signal, traffic_byt, speed_mbps, d_speed_mbps,residual_bw, weight, confirmed, wired)

	@Pyro4.oneway
	def remove_node(self, n):
		self.gnet_graph.remove_node(n)

	def get_node_edges_update_state(self, node, attr='signal'):
		self.gnet_graph.get_node_edges_update_state(node, attr)

	@Pyro4.oneway
	def update_edges_of_node(self, node, assoc_list):
		self.gnet_graph.update_edges_of_node(node, assoc_list)

	def get_time_stamp(self):
		return self.gnet_graph.time_stamp

	def number_of_nodes(self):
		return self.gnet_graph.number_of_nodes()

	def nodes(self):
		return self.gnet_graph.nodes(data=True)

	def edges(self):
		return self.gnet_graph.edges(data=True)

	def path(self,src_ip, dst_ip):
		path = self.gnet_graph.path(src_ip,dst_ip)
		return "the gpath is %s" % path


	def get_output(self):
		return self.output
		
	def get_gnet_graph(self):
		Pyro4.util.SerializerBase.register_class_to_dict(GNetGraph,self.mything_dict)
		Pyro4.util.SerializerBase.register_dict_to_class("BORABAHIA", self.mything_creator)
		return self.gnet_graph

	def mything_dict(self,obj):
		return {"__class__": "BORABAHIA","time": obj.time_stamp}

	def mything_creator(self,classname,d):
		return GNetGraph(d["time"])


	def set_nome(self,nome):
		self.nome = nome

	def get_nome(self):
		return "My name is %s" % self.nome


host = ni.ifaddresses('ofsw0')[2][0]['addr']
daemon = Pyro4.Daemon(host=host,port=47922)                # make a Pyro daemon
uri = daemon.register(global_ofcl_app,"global_ofcl_app")   # register the greeting maker as a Pyro object

fo = open("/tmp/uri.txt","wb")
fo.write(str(uri) )
fo.close()
#print uri      # print the uri so we can use it in the client later
daemon.requestLoop()                   # start the event loop of the server to wait for calls