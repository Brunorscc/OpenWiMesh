#/home/openwimesh/capturas/42/dump-flows/self-to-ctlr

#calculate delay slowpath

# cat 192.168.199.1 | sed '/Unreachable/d' | grep 'seq=1\|seq=2' | awk -F'=' '{print $2,$4}'| cut -d' ' -f1,3

from __future__ import with_statement
import math
from os import walk
import sys
import fileinput

#def get_stats(MAC, diff_list):   
#  n = float(len(diff_list))
##  mean = sum(diff_list)/n
#  stdev = 0
#  for value in diff_list:
#    stdev += (value - mean)**2
##  stdev = math.sqrt(stdev/(n))
 # print "%s, MIN: %f, MAX: %f, MEDIA: %f, DESVIO: %f" % (MAC, min(diff_list), max(diff_list), mean, stdev)

#def get_stats(tipo, lista, intervalo=5, agreg=30):
def get_stats(tipo, lista, lista_g, nome, tira_media=0, printar=0): 
	stdev = 0
  	diff_list=[]
  	aux = 0
  	aux2 = 0
	#print "LISTA= %s" % lista
	# Create the list of diff_list
	n = int(len(lista))
	atual = 0
	#print "pos 1 - %s  - pos 2 %s " % (lista[0], lista[1])
	
	# TODO: MUDAR RESULTADO COM BASE NO INTERVALO DAS COLETAS E AGREGACAO DESEJADA
	# interv = int(agreg/intervalo)
	# 
	# if interv > 1:
	# cont = 0
	# sum_aux = 0
	# list_aux=[]
	# for i in range(0,n-1)
	# 
	# 	cont++
	# 	if cont == interv:
	#		
	#
	if n > 1:
		if tira_media == 0:
			for atual in range(0,n-1):
				aux = float(lista[atual])
				#print "atual = %s" % aux
				aux2 = float(lista[atual+1]) - aux
				diff_list.append(aux2)
		else:
			for atual in range(0,n):
				diff_list.append(float(lista[atual]))	 
				#print "AUX - %s  AUX2 - %s" % (aux, aux2)
		#print ("%s LIST - %s" % (tipo, diff_list))
		n = float(len(diff_list))
		mean = sum(diff_list)/n
		for value in diff_list:
			stdev += (value - mean)**2
		stdev = math.sqrt(stdev/(n))

		
		if lista_g.has_key("media"):
			lista_g["media"].append(mean)
		else:
		    lista_g["media"] = [mean]

		if lista_g.has_key("desvio"):
			lista_g["desvio"].append(stdev)
		else:
			lista_g["desvio"] = [stdev]
		#print ""
		#print "DIFF_LIST - %s" % diff_list
		if printar == 1:
			print "%s-%s, MIN: %.4f/s, MAX: %.4f/s, MEDIA: %.4f/s, DESVIO: %.4f" % (nome, tipo, min(diff_list), max(diff_list),mean, stdev)
	else:
		pass
		#print "Tamanho da lista de valores de '%s' de %s e' menor que 1" % (tipo,nome)

def get_stats_agg(tipo, lista, start, finish): 
	n = int(len(lista))
	if n > 0:
		mean = sum(lista)/n
		stdev = 0
		for value in lista:
			stdev += (value - mean)**2
		stdev = math.sqrt(stdev/(n))
		print "AGREGADO da Amostra %s-%s - %s, MIN: %.4f/s, MAX: %.4f/s, MEDIA: %.4f/s, DESVIO: %.4f" % (start, finish,tipo, min(lista)/30, max(lista)/30, mean/30, stdev/30)
	else:
		pass
		#print "Tamanho da lista de valores de '%s' e' menor que 1" % tipo

def main():
	f_dict = []
	arg = sys.argv
	#print ("ARG: %s" % arg[1])

	# ARG[1] e o FULLPATH do diretorio onde esta o arquivo ja tratado no formato:
	# packetcount" "bytecount
	# EX:
	# linha1: '12  1230'
	# linha2: . . .

	path = arg[1]
	start = int(arg[2])
	finish = int(arg[3])
	path2 = arg[4]
	x = None

	#print "start %d - finish %d" % (start, finish)

	pkt_list_agg={'media':[],'desvio':[]}
	byte_list_agg={'media':[],'desvio':[]}

	for i in range(start,finish+1):
		f_dict = []
		#print "I = %d" % i
		for (dirpath, dirnames, filenames) in walk("%s/%s/%s" % (path,i,path2)):
		    f_dict.extend(filenames)
		    break

		#print "FILES: %s" % (f_dict)

		pkt_list_g={'media':[],'desvio':[]}
		byte_list_g={'media':[],'desvio':[]}

		#ABRE ARQUIVO
		for x in f_dict:
		  with open('%s/%s/%s/%s' % (path,i,path2,x)) as f:
		    #print "FILE: %s" % x
		    #f.readline()
		    #print "READLINE = %s" % f.readline()
		    
		    # LISTA LOCAL DE CADA ARQUIVO
		    pkt_list = []
		    byte_list = []

		    for line in f.readlines():
		    	pktcount, bytecount = line.split(' ')
		    	pkt_list.append(pktcount)
		    	byte_list.append(bytecount)
		    	#print "LINE - %s" % line
		  #  pkt_list.append(pktcount)
		#    byte_list.append(bytecount)
		    get_stats("pktcount", pkt_list,pkt_list_g, x, 0)
		    get_stats("bytecount", byte_list,byte_list_g, x, 0)
		#    print ""
		    


		#      MAC = MAC.strip()
		#     if diff_list.has_key(MAC):
		#        diff_list[MAC].append(value)
		#   else:
		#      diff_list[MAC] = [value]
		#for k,v in diff_list.items():
		 # get_stats(k,v)

		#print "G MEDIA list - %s" % (pkt_list_g['media'])
		#print "G BYTE list - %s" % (byte_list_g['media'])
		#print ""
		get_stats("pktcount", pkt_list_g['media'], pkt_list_agg, i, 1,1)
		get_stats("bytecount", byte_list_g['media'], byte_list_agg, i, 1,1)
		#print ""
	get_stats_agg("pktcount", pkt_list_agg['media'], start, finish)
	get_stats_agg("bytecount", byte_list_agg['media'], start, finish)

	#print "PKT - LIST %s" % pkt_list_agg
	#print "BYTE - LIST %s" % byte_list_agg

if __name__=="__main__":
	main()