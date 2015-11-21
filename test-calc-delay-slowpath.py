#calculate std variation

# STILL UNDER DEVELOPMENT..
# NECESSITA DE NOVA CAPTURA DE PINGS NAO ALEATORIOS
# PING DE CADA NO' PARA OUTROS NO'S FIXOS EM OUTROS DOMINIOS 
# DOMINIOS ESTES: LOCAL, VIZINHO E APOS UM DOMINIO VIZINHO (SE POSSIVEL) 
# E COM CONTROLADORES FIXOS DE PREFERENCIA
# 

from __future__ import with_statement
import math
from os import walk
import sys

f_dict = []
arg = sys.argv
print ("ARG: %s" % arg[1])
for (dirpath, dirnames, filenames) in walk("/home/openwimesh/capturas/%s/filter-slowpath" % arg[1]):
    f_dict.extend(filenames)
    break

print "FILES: %s" % (f_dict)

for x in f_dict:
  	with open('/home/openwimesh/capturas/%s/filter-slowpath/%s' % (arg[1],x)) as f:
	  	print ("FILE: %s" % x)
	  	#f.readline()
	  	stdev = 0
	  	cont = 1
	  	latencies=[]
	  	aux = 0
		# Create the list of latencies
		for value in f.readlines():
			if cont == 1:
				aux = float(value)
				cont+=1
			else:
				aux = aux - float(value)
				cont=1
				latencies.append(aux)
		print ("SLOWPATH LIST - %s" % latencies)
		n = float(len(latencies))
		mean = sum(latencies)/n
		for value in latencies:
			stdev += (value - mean)**2
		stdev = math.sqrt(stdev/(n))
		print "%s, MEDIA: %f, DESVIO: %f" % (x, mean, stdev)