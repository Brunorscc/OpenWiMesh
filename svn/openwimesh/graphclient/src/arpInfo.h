/* 
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
 */

#ifndef ARPINFO_H
#define	ARPINFO_H

#ifdef	__cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
//#include <sys/types.h>
//#include <sys/socket.h>
//#include <sys/ioctl.h>
#include "associations.h"

#define _PATH_PROCNET_ARP       "/proc/net/arp"

struct chainedListEntry {
    void *current;
    struct chainedListEntry *next;
};

struct chainedList {
    int count;                          // Current number of entries.    
    struct chainedListEntry *begin;      // Chain.
    struct chainedListEntry *end;        // Chain.
};

struct macIpPair {
    char *mac;
    char *ip;
};

void addToChainedList(struct chainedList *list, void *data);
void clearChainedList(struct chainedList *list);
int getArpForIntf(char *intf, struct chainedList *arpTable);
void printArpTable(struct chainedList *arpTable);
void delArpEntriesIfNotAtReach(struct chainedList *arpTable, associationListTp *assocPt, char *dev);
int delArpEntry(char *ip, char *dev);
void clearArpTable(char *dev, struct chainedList *arpTable);
void initArpTableList(struct chainedList *arpTable);

#ifdef	__cplusplus
}
#endif

#endif	/* ARPINFO_H */

