#calculate std variation
#

from __future__ import with_statement
import math
from os import walk
import sys

def get_stats(MAC, latencies):   
  n = float(len(latencies))
  mean = sum(latencies)/n
  stdev = 0
  for value in latencies:
    stdev += (value - mean)**2
  stdev = math.sqrt(stdev/(n))
  print "%s, MIN: %f, MAX: %f, MEDIA: %f, DESVIO: %f" % (MAC, min(latencies), max(latencies), mean, stdev)

f_dict = []
arg = sys.argv
print ("ARG: %s" % arg[1])
for (dirpath, dirnames, filenames) in walk("/home/openwimesh/capturas/%s/latencia/" % arg[1]):
    f_dict.extend(filenames)
    break

print "FILES: %s" % (f_dict)

for x in f_dict:
  with open('/home/openwimesh/capturas/%s/latencia/%s' % (arg[1],x)) as f:
    print "FILE: %s" % x
    f.readline()
    # Create the list of latencies
    latencies = {}
    for line in f.readlines():
      MAC, timestamp, value = line.split(',')
      value = float(value.strip())
      MAC = MAC.strip()
      if latencies.has_key(MAC):
          latencies[MAC].append(value)
      else:
          latencies[MAC] = [value]
    for k,v in latencies.items():
      get_stats(k,v)  