import Pyro4
import netifaces as ni
import time
from gnet_graph import GNetGraph
import os
import unittest



@Pyro4.expose(instance_mode="single")
class global_ofcl_app(object):
	"""docstring for global_ofcl_app"""
	def __init__(self):
		self.gnet_graph = GNetGraph()
		self.nome = None
		self.ip_addr = ni.ifaddresses('ofsw0')[2][0]['addr']
		self.hw_addr = ni.ifaddresses('ofsw0')[17][0]['addr']
		self.cid = 0
		self.ip_ofct_list=list(range(225,253))
		self.becoming_ofctl = []
		self.connecting_nodes = {}

	def becoming_ofctl(self):
		return self.becoming_ofctl

	@Pyro4.oneway
	def add_becoming_ofctl(self,sw_mac):
		self.becoming_ofctl.append(sw_mac)

	def del_becoming_ofctl(self,sw_mac):
		self.becoming_ofctl.remove(sw_mac)

	def get_ofctl_free_ip(self):
		free_ip="192.168.199."
		free_ip+=str(self.ip_ofct_list.pop())
		return free_ip

	def check_arp_req_to_ofctl(self,orig_src_hw,dst_node_ip):
		if orig_src_hw in self.gnet_graph.nodes():
			return "connected"
		if orig_src_hw in self.connecting_nodes:
			return "connecting"
		self.connecting_nodes[orig_src_hw]= {'ofctl_ip': dst_node_ip}
		return "ok"

	def check_creating_new_ofctl(self,cid):
		nodes= get_node_list_by_attr('cid', cid)
		if len(nodes) > 3:
			pass

	@Pyro4.oneway
	def add_ofctl(self,cid,ofctl_hw,ofctl_ip):
		self.gnet_graph.update_ofctl_list(cid,ofctl_hw,ofctl_ip)

	def get_cid_free(self):
		self.cid += 1
		return self.cid

	def get_fortune(self,name):
		return self.gnet_graph.get_fortune(name)

	@Pyro4.oneway
	def add_node(self, hwaddr, ip=None, cid=None):
		self.gnet_graph.add_node(hwaddr, ip, cid)
		if hwaddr in self.connecting_nodes:
			del self.connecting_nodes[hwaddr]

	@Pyro4.oneway
	def add_edge(self, source_mac, target_mac, signal=None, traffic_byt=None, speed_mbps=None, d_speed_mbps=None,residual_bw=None, weight=None, confirmed=True, wired=False):

		self.gnet_graph.add_edge(source_mac, target_mac, signal, traffic_byt, speed_mbps, d_speed_mbps,residual_bw, weight, confirmed, wired)

	#@Pyro4.oneway
	def remove_node(self, n, c):
		cid = -1
		try:
			cid = self.gnet_graph.get_node_cid(n)
			if cid == c:
				self.gnet_graph.remove_node(n)
				return "ok"
		except Exception as e:
			return "erro %s, n=%s,c=%s,cid=%s" % (e,n,c,cid)

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
		edges = self.gnet_graph.edges(data=True)
		l=[]
		for e in edges:
			ll = [e[0],e[1]]
			l.append(ll)
		return l

	def path(self,src_ip, dst_ip):
		path = self.gnet_graph.path(src_ip,dst_ip)
		return path


	def get_ip_addr(self):
		return self.ip_addr

	def get_hw_addr(self):
		return self.hw_addr
		
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