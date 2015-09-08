import Pyro4
import netifaces as ni
import time
from gnet_graph import GNetGraph

gnet_graph = GNetGraph()


host = ni.ifaddresses('ofsw0')[2][0]['addr']
daemon = Pyro4.Daemon(host=host,port=41922)                # make a Pyro daemon
uri = daemon.register(gnet_graph,"global_ofcl_app")   # register the greeting maker as a Pyro object

fo = open("/tmp/uri.txt","wb")
fo.write(str(uri) )
fo.close()
#print uri      # print the uri so we can use it in the client later
daemon.requestLoop()                   # start the event loop of the server to wait for calls