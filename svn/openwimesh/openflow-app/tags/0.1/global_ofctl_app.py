import Pyro4
import netifaces as ni
import time

class GreetingMaker(object):
    def get_fortune(self, name):
        return "Hello, {0}. Here is your fortune message:\n" \
               "Behold the warranty -- the bold print giveth and the fine print taketh away.".format(name)


host = ni.ifaddresses('ofsw0')[2][0]['addr']
daemon = Pyro4.Daemon(host=host,port=41922)                # make a Pyro daemon
uri = daemon.register(GreetingMaker,"global_ofcl_app")   # register the greeting maker as a Pyro object

fo = open("/tmp/uri.txt","wb")
fo.write(str(uri) )
fo.close()
#print uri      # print the uri so we can use it in the client later
daemon.requestLoop()                   # start the event loop of the server to wait for calls