import Pyro4
import netifaces as ni
import time
from gnet_graph import GNetGraph
import os
import unittest
import random
import logging



@Pyro4.expose(instance_mode="single")
class global_ofcl_app(object):
	"""docstring for global_ofcl_app"""
	# timeout for confirm an edge
	CONFIRM_OFCTL_TOUT = 10

	def __init__(self):

		logging.info('Starting global_ofcl_app')
		self.gnet_graph = GNetGraph()
		self.nome = None
		self.ip_addr = ni.ifaddresses('ofsw0')[2][0]['addr']
		self.hw_addr = ni.ifaddresses('ofsw0')[17][0]['addr']
		self.cid_counter = 0
		self.gcid = None
		self.ip_ofct_list=list(range(225,253))
		self.becoming_ofctl = {}
		self.connecting_nodes = {}
		self.creating_new_ofctl_task_list = {}
		self.new_ofctls_lock = False

	@Pyro4.oneway
	def set_gcid(self,gcid):
		self.gcid = gcid

	@Pyro4.oneway
	def check_ofctl_conn(self):
		while True :
			logging.debug('checking ofctl connection')
			if self.gnet_graph.ofctl_list:
				dead = []
				try:
					for cid in self.gnet_graph.ofctl_list:
						now = time.time()
						#logging.debug("now is %s",now)
						#logging.debug("ofctl %s time %s",cid,self.gnet_graph.ofctl_list[cid]['last_update'])
						logging.debug("delay from %s is %s",cid, now - self.gnet_graph.ofctl_list[cid]['last_update'])
						
						if now - self.gnet_graph.ofctl_list[cid]['last_update'] > self.CONFIRM_OFCTL_TOUT:
							dead.append(cid)
							#ofctl_hw = self.gnet_graph.ofctl_list[cid]['hwaddr']
					
					for cid in dead:
						nodes= self.gnet_graph.get_node_list_by_attr('cid', cid)
						for node in nodes:
							logging.debug('Removing node %s',node)
							self.gnet_graph.remove_node(node)
						logging.debug('Removing ofctl %s', cid)
						ofctl_ip = self.gnet_graph.ofctl_list[cid]['ipaddr']
						self.ip_ofct_list.append(ofctl_ip.split('.')[3])
						self.gnet_graph.remove_ofctl(cid)

					logging.debug("Nodes %s",self.gnet_graph.nodes(data=True))
							
				except Exception as e:
					logging.debug("Problema %s",e)

			try:
				dead = []
				for node in self.connecting_nodes:
					now = time.time()
					if now - self.connecting_nodes[node]['time'] > 8:
						dead.append(node)

				for node in dead:
					del self.connecting_nodes[node]
			except Exception as e:
				logging.debug("Problema remover connecting_nodes (%s)",e)

			try:
				dead = []
				for node in self.becoming_ofctl:
					now = time.time()
					if now - self.becoming_ofctl[node] > 20:
						dead.append(node)
				for node in dead:
					self.del_becoming_ofctl(node)
			except Exception as e:
				logging.debug("Problema remover becoming_ofctl (%s)",e)

			try:
				self.new_ofctls()
			except Exception as e:
				logging.debug("Problema add new ofctls (%s)",e)

			try:
				nodes_without_cid = self.gnet_graph.check_by_attr_cid()
				for cada in nodes_without_cid:
					logging.debug("Removendo node sem CID %s", cada)
					self.gnet_graph.remove_node(cada)
			except Exception as e:
				logging.debug("ERRO Removendo node sem CID (%s)", e)

			logging.debug("sleeping")
			time.sleep(5)


	def add_becoming_ofctl(self,sw_mac):
		logging.debug('%s will be an ofctl',sw_mac)
		self.becoming_ofctl[sw_mac] = time.time()

	def del_becoming_ofctl(self,sw_mac):
		if sw_mac in self.becoming_ofctl:
			logging.debug('delete %s from becoming_ofctl',sw_mac)
			del self.becoming_ofctl[sw_mac]

	def get_ofctl_free_ip(self):
		free_ip="192.168.199."
		free_ip+=str(self.ip_ofct_list.pop())
		logging.debug("%s will release",free_ip)
		return free_ip

	def check_arp_req_to_ofctl(self,cid,orig_src_hw,dst_node_ip,recv_node_hw):
		logging.debug('ARP request from ofctl %s, who-has-%s-tell-%s',cid,dst_node_ip,orig_src_hw)
		if orig_src_hw in self.gnet_graph.nodes():
			return "connected"
		if orig_src_hw in self.connecting_nodes:
			return "connecting"
		if recv_node_hw in self.becoming_ofctl:
			return "becoming_ofctl"

		self.connecting_nodes[orig_src_hw]= {'cid': cid, 'time': time.time()}
		logging.debug("self.gnet_graph.ofctl_list[cid]['ipaddr'] != 192.168.199.254 is %s",(self.gnet_graph.ofctl_list[cid]['ipaddr'] != '192.168.199.254'))
		if self.gnet_graph.ofctl_list[cid]['ipaddr'] != '192.168.199.254':
			logging.debug("%s will take over control sw (%s)",self.gnet_graph.ofctl_list[cid]['ipaddr'],orig_src_hw)
			return 'fake'
		return "ok"

	@Pyro4.oneway
	def update_nodes(self,cid,nl):
			logging.debug("update ofct %s nodes list", cid)
			nodes = self.gnet_graph.get_node_list_by_attr('cid', cid)

			local_nodes = []
			for n in nl:
				local_nodes.append(n[0])

			remove_list = list(set(nodes)-set(local_nodes))
			add_list= list(set(local_nodes)-set(nodes))
			
			#remove_list = [a for a in nodes if a not in nl]
			#add_list = [a for a in <lista-local> if a not in <lista-global>]

			for node in remove_list:
					logging.debug("remove node %s", node)
					
					#TROCAR LINHA ABAIXO POR: self.gnet_graph.remove_node(node[0])
					
					self.gnet_graph.remove_node(node)
			logging.debug("NL - %s", nl)
			logging.debug("NODES - %s", nodes)
			logging.debug("Remove LIST - %s", remove_list)
			logging.debug("ADD LIST - %s", add_list)

			try:
				for node in add_list:
					logging.debug("add node %s", node)
					IP = None
					for n in nl:
						if n[0] == node:
							IP=n[1]
					if IP:
						self.add_node(node, IP, cid)
					#TROCAR LINHA ABAIXO POR: self.gnet_graph.remove_node(node[0])
			except Exception as e:
				logging.debug("Erro add_node no grafo global pq detectou no grafo - %s", e)
				

	def new_ofctls(self):
		self.new_ofctls_lock = True
		try:
			if self.gnet_graph.ofctl_list:
				for cid in self.gnet_graph.ofctl_list:
					nodes= self.gnet_graph.get_node_list_by_attr('cid', cid)
					ofctl_hw = self.gnet_graph.ofctl_list[cid]['hwaddr']
					try: 
						nodes.remove(ofctl_hw)
					except Exception as e:
						logging.debug("Erro remove nodes (%e) - nodes = %s - ofctl_hw = %s", e,nodes, ofctl_hw)

					nodes = list(set(nodes) - set(self.becoming_ofctl.keys()))
					new_ofctls_list = self.gnet_graph.get_node_list_by_path_len(nodes,cid)
					logging.debug("NODES - OFCTLS LIST - %s", nodes)
					logging.debug("NEW OFCTLS LIST - %s", new_ofctls_list)
					if len(new_ofctls_list) > 0:
						X = random.choice(new_ofctls_list)
						logging.debug("RANDOM CHOICE OFCTLS LIST - X -%s", X)
						l = [X]
						logging.debug("RANDOM CHOICE OFCTLS LIST - L - %s", l)
						self.creating_new_ofctl_task_list[cid]= l
						continue
					
					#nodes = list(set(nodes) - set(new_ofctls_list))

					if len(nodes) > 3:
						self.creating_new_ofctl_task_list[cid] = [random.choice(nodes)]
		except Exception as e:
			logging.debug("Erro generating new_ofctls_list (%s)",e)
		self.new_ofctls_lock = False

	def get_new_ofctls_list(self,cid):
		if not self.new_ofctls_lock:
			if cid in self.creating_new_ofctl_task_list:
				new_ofctls_list = self.creating_new_ofctl_task_list[cid]
				logging.debug("ofctl %s has new_ofctls %s",cid,new_ofctls_list)
				return new_ofctls_list
		
		return []



	def check_creating_new_ofctl(self,cid):
		if cid not in self.gnet_graph.ofctl_list:
			return None
		nodes= self.gnet_graph.get_node_list_by_attr('cid', cid)


		
		#if sum([ i in nodes for i in self.becoming_ofctl]):


		ofctl_hw = self.gnet_graph.ofctl_list[cid]['hwaddr']
		try: 
			nodes.remove(ofctl_hw)
		except Exception as e:
			logging.debug("Erro remove nodes (%e) - nodes = %s - ofctl_hw = %s", e,nodes, ofctl_hw) 

		if len(nodes) - sum([ i in nodes for i in self.becoming_ofctl]) > 2:			
			new_ofctl_hw = random.choice(nodes)
			if new_ofctl_hw in self.becoming_ofctl:
				return None
			self.add_becoming_ofctl(new_ofctl_hw)
			logging.debug("%s will be ofctl",new_ofctl_hw)
			return new_ofctl_hw
		
		return None

	def get_crossdomain(self,src_ip,dst_ip,cid):
		logging.debug('ofctl %s request the crossdomain link for reach %s',cid,dst_ip)
		path = self.gnet_graph.path(src_ip,dst_ip)
		if len(path)== 0:
			logging.debug('There is no path %s -> %s ',src_ip,dst_ip)
			return None
		for i,sw in enumerate(path):
			if self.gnet_graph.get_node_cid(path[i+1]) != cid:
				crossd = {'my_sw': path[i], 'dst_sw': path[i+1]}
				logging.debug('The path from %s to %s is through the crossdomain link(%s-%s)',src_ip,dst_ip,path[i],path[i+1])
				return crossd

	@Pyro4.oneway
	def send_tstamp(self,cid,tstamp):
		delay = time.time() - tstamp
		logging.debug("Delay_CTRL,%s,%s", cid, delay)

	@Pyro4.oneway
	def add_ofctl(self,cid,ofctl_hw,ofctl_ip):
		logging.info('the ofctl %s, %s, %s',cid,ofctl_ip,ofctl_hw)
		self.gnet_graph.update_ofctl_list(cid,ofctl_hw,ofctl_ip)
		self.gnet_graph.ofctl_list[cid]['last_update'] = time.time()
		logging.debug("ofctl %s time %s",cid,self.gnet_graph.ofctl_list[cid]['last_update'])
		
		self.del_becoming_ofctl(ofctl_hw)

	def get_cid_free(self):
		self.cid_counter += 1
		return self.cid_counter

	def get_fortune(self,name):
		return self.gnet_graph.get_fortune(name)

	def send_latency(self):
		now = time.time()
		return now

	@Pyro4.oneway
	def add_node(self, hwaddr, ip=None, cid=None):
		logging.debug('Adding node %s at ofctl %s',hwaddr,cid)
		self.gnet_graph.add_node(hwaddr, ip, cid)
		if hwaddr in self.connecting_nodes:
			del self.connecting_nodes[hwaddr]

	@Pyro4.oneway
	def add_edge(self, source_mac, target_mac, signal=None, traffic_byt=None, speed_mbps=None, d_speed_mbps=None,residual_bw=None, weight=None, confirmed=True, wired=False):

		logging.debug('Adding edge %s -> %s',source_mac,target_mac)
		self.gnet_graph.add_edge(source_mac, target_mac, signal, traffic_byt, speed_mbps, d_speed_mbps,residual_bw, weight, confirmed, wired)

	@Pyro4.oneway
	def remove_node(self, n, c):
		cid = -1
		try:
			cid = self.gnet_graph.get_node_cid(n)
			if cid == c and n not in self.becoming_ofctl:
				logging.debug('Removing node %s',n)
				self.gnet_graph.remove_node(n)
		except Exception as e:
			logging.debug("erro removing node (%s), n=%s,c=%s,cid=%s",e,n,c,cid)

	def get_node_edges_update_state(self, node, attr='signal'):
		self.gnet_graph.get_node_edges_update_state(node, attr)

	@Pyro4.oneway
	def update_edges_of_node(self,cid, node, assoc_list):
		logging.debug("Update from ofctl %s",cid)
		#logging.debug("ofctl %s time before %s",cid,self.gnet_graph.ofctl_list[cid]['last_update'])
		self.gnet_graph.ofctl_list[cid]['last_update'] = time.time()
		#logging.debug("ofctl %s time after %s",cid,self.gnet_graph.ofctl_list[cid]['last_update'])
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



logging.basicConfig(filename='global_ofcl_app.log',level=logging.DEBUG)
host = ni.ifaddresses('ofsw0')[2][0]['addr']
daemon = Pyro4.Daemon(host=host,port=47922)                # make a Pyro daemon
uri = daemon.register(global_ofcl_app,"global_ofcl_app")   # register the greeting maker as a Pyro object
logging.info('The global_ofcl_app uri is %s',uri)
fo = open("/tmp/uri.txt","wb")
fo.write(str(uri) )
fo.close()
#print uri      # print the uri so we can use it in the client later
daemon.requestLoop()                   # start the event loop of the server to wait for calls