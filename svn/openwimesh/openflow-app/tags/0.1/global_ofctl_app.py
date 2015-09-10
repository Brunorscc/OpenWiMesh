import Pyro4
import netifaces as ni
import time
from gnet_graph import GNetGraph
import os



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


	def get_output(self):
		return self.output
		

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