"""
   OpenWiMesh - Framework for Software Defined Wireless Mesh Networks
   Copyright (C) 2013-2014  GRADE - http://grade.dcc.ufba.br

   This file is part of OpenWiMesh.

   OpenWiMesh is free software: you can redistribute it and/or modify
   it under the terms of the GNU Affero General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   OpenWiMesh is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU Affero General Public License
   along with OpenWiMesh.  If not, see <http://www.gnu.org/licenses/>.

   Linking this library statically or dynamically with other modules is
   making a combined work based on this library.  Thus, the terms and
   conditions of the GNU Affero General Public License cover the whole
   combination.

   As a special exception, the copyright holders of this library give you
   permission to link this library with independent modules to produce an
   executable, regardless of the license terms of these independent
   modules, and to copy and distribute the resulting executable under
   terms of your choice, provided that you also meet, for each linked
   independent module, the terms and conditions of the license of that
   module.  An independent module is a module which is not derived from
   or based on this library.  If you modify this library, you may extend
   this exception to your version of the library, but you are not
   obligated to do so.  If you do not wish to do so, delete this
   exception statement from your version.
"""

import time
import re
import socket
import sys, os

# Add current directory to path
sys.path.append(os.getcwd())

from net_graph import NetGraph

n = NetGraph()
# No no qual o graphClient estara executando
sw = 'e0:06:e6:dc:7d:d7'
n.add_node(sw)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 1111))

pattern = "(\w+)\|([^|]+)\|([\d-]+)\|(\d+)\|([\d\.]+)\|([\d\.]+)"

while True:
    data, addr = sock.recvfrom(10240)
    assoc_list = []
    for s in data.split(';'):
        result = re.match(pattern, s)
        if result:
            assoc_list.append(result.groups())
        else:
            print "WARNING: malformed packet 1111/UDP (graphClient)"

    n.update_edges_of_node(sw, assoc_list)
    print "edge: ", str(n.edge[sw])
