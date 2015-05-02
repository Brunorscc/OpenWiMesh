/* 
 * File:   arpInfo.c
 * Author: sldlg
 *
 * Created on April 8, 2013, 4:02 PM
 *
 * This Library is based on the following source code.
 * Full disclosure of its licensing requirements also follows.
 */

/*
 * arp          This file contains an implementation of the command
 *              that maintains the kernel's ARP cache.  It is derived
 *              from Berkeley UNIX arp(8), but cleaner and with sup-
 *              port for devices other than Ethernet.
 *
 * NET-TOOLS    A collection of programs that form the base set of the
 *              NET-3 Networking Distribution for the LINUX operating
 *              system.
 *
 * Version:     $Id: arp.c,v 1.20 2001/04/08 17:05:05 pb Exp $
 *
 * Maintainer:  Bernd 'eckes' Eckenfels, <net-tools@lina.inka.de>
 *
 * Author:      Fred N. van Kempen, <waltje@uwalt.nl.mugnet.org>
 *
 * Changes:
 *              (based on work from Fred N. van Kempen, <waltje@uwalt.nl.mugnet.org>)
 *              Alan Cox        :       modified for NET3
 *              Andrew Tridgell :       proxy arp netmasks
 *              Bernd Eckenfels :       -n option
 *              Bernd Eckenfels :       Use only /proc for display
 *       {1.60} Bernd Eckenfels :       new arpcode (-i) for 1.3.42 but works 
 *                                      with 1.2.x, too
 *       {1.61} Bernd Eckenfels :       more verbose messages
 *       {1.62} Bernd Eckenfels :       check -t for hw adresses and try to
 *                                      explain EINVAL (jeff)
 *970125 {1.63} Bernd Eckenfels :       -a print hardwarename instead of tiltle
 *970201 {1.64} Bernd Eckenfels :       net-features.h support
 *970203 {1.65} Bernd Eckenfels :       "#define" in "#if", 
 *                                      -H|-A additional to -t|-p
 *970214 {1.66} Bernd Eckenfels :       Fix optarg required for -H and -A
 *970412 {1.67} Bernd Eckenfels :       device=""; is default
 *970514 {1.68} Bernd Eckenfels :       -N and -D
 *970517 {1.69} Bernd Eckenfels :       usage() fixed
 *970622 {1.70} Bernd Eckenfels :       arp -d priv
 *970106 {1.80} Bernd Eckenfels :       new syntax without -D and with "dev <If>",
 *                                      ATF_MAGIC, ATF_DONTPUB support. 
 *                                      Typo fix (Debian Bug#5728 Giuliano Procida)
 *970803 {1.81} Bernd Eckenfels :       removed junk comment line 1
 *970925 {1.82} Bernd Eckenfels :       include fix for libc6
 *980213 (1.83) Phil Blundell:          set ATF_COM on new entries
 *980629 (1.84) Arnaldo Carvalho de Melo: gettext instead of catgets
 *990101 {1.85} Bernd Eckenfels		fixed usage and return codes
 *990105 (1.86) Phil Blundell:		don't ignore EINVAL in arp_set
 *991121 (1.87) Bernd Eckenfels:	yes --device has a mandatory arg
 *010404 (1.88) Arnaldo Carvalho de Melo: use setlocale
 *
 *              This program is free software; you can redistribute it
 *              and/or  modify it under  the terms of  the GNU General
 *              Public  License as  published  by  the  Free  Software
 *              Foundation;  either  version 2 of the License, or  (at
 *              your option) any later version.
 */

#include "arpInfo.h"

void addToChainedList(struct chainedList *list, void *data) {
    if (data && list) {
        struct chainedListEntry *entry = malloc(sizeof (struct chainedListEntry));
        entry->current = data;
        entry->next = NULL;
        if (list->count > 0)
            list->end->next = entry; // Makes the current end point to new end, only if not first entry.
        list->end = entry; // Defines the current end in list to added entry.
        list->end->next = NULL;
        if (list->count == 0)
            list->begin = list->end; // If first entry, define begin of list.
        list->count++; // Increment counter.
    }
}

void clearChainedList(struct chainedList *list) {
//    int i;
    struct chainedListEntry *lastBegin;
    struct macIpPair *macIp;
    while (list->begin) {
        macIp = list->begin->current;
        free(macIp->mac);
        free(macIp->ip);
        free(list->begin->current);
        lastBegin = list->begin;
        list->begin = list->begin->next;
        free(lastBegin);
    }
}

// Initializes the data structure which holds the ARP table
void initArpTableList(struct chainedList *arpTable) {
    arpTable->begin = NULL;
    arpTable->end = NULL;
    arpTable->count = 0;
}

/* Display the contents of the ARP cache in the kernel. */
int getArpForIntf(char *intf, struct chainedList *arpTable) {
    char ip[100];
    char hwa[100];
    char mask[100];
    char line[200];
    char dev[100];
    int type, flags;
    FILE *fp;
    int num;

    /* Open the PROCps kernel table. */
    if ((fp = fopen(_PATH_PROCNET_ARP, "r")) == NULL) {
        perror(_PATH_PROCNET_ARP);
        return (-1);
    }
    /* Bypass header -- read until newline */
    if (fgets(line, sizeof (line), fp) != (char *) NULL) {
        strcpy(mask, "-");
        strcpy(dev, "-");
        /* Read the ARP cache entries. */
        for (; fgets(line, sizeof (line), fp);) {
            num = sscanf(line, "%s 0x%x 0x%x %100s %100s %100s\n",
                    ip, &type, &flags, hwa, mask, dev);
            if (num < 4)
                break;

            /* if the user specified device differs, skip it */
            if (intf[0] && strcmp(dev, intf))
                continue;
            else {
                int size = strlen(hwa) + 1;
                char *macAddr = malloc(size);
                strncpy(macAddr, hwa, size);
                size = strlen(ip) + 1;
                char *ipAddr = malloc(size);
                strncpy(ipAddr, ip, size);
                struct macIpPair *st = malloc(sizeof(struct macIpPair));
                st->mac = macAddr;
                st->ip = ipAddr;
                addToChainedList(arpTable, st);
            }
        }
    }
    return (0);
}

void printArpTable(struct chainedList *arpTable) {
    int i = 1;
    struct chainedListEntry *addr = arpTable->begin;
    struct macIpPair *st;
    while (addr) {
        st = addr->current;
        printf("Arp entry %d -> %s, for IP -> %s\n", i, st->mac, st->ip );
        addr = addr->next;
        i++;
    }
}

void clearArpTable(char *dev, struct chainedList *arpTable) {
    int i = 1;
    struct chainedListEntry *addr = arpTable->begin;
    struct macIpPair *st;
    while (addr) {
        st = addr->current;
        delArpEntry(st->ip, dev);
        // Remove this log later !!!
        printf("    Cleaning ARP entries for IP %s and Interface %s\n",st->ip, dev);
        addr = addr->next;
        i++;
    }
}

void delArpEntriesIfNotAtReach(struct chainedList *arpTable, associationListTp *assocPt, char *dev) {
    struct chainedListEntry *addr = arpTable->begin;
    while (addr) {
        int ret;
        bool notFound = true; // Initially not yet found
        associatedIBSSTp *assocItem = assocPt->begin;
        while (assocItem) {
            ret = strcasecmp(addr->current, assocItem->bssid);
            if (!ret) { // if found, mark and exit loop
                notFound = false;
                break;
            }
            assocItem = assocItem->next;
        }
        if (notFound) {
            // Remove arp entry from cache.
            struct macIpPair *macIp = addr->current;
            ret = delArpEntry(macIp->ip, dev);
            if (!ret)
                printf("Removed arp entry -> %s | %s\n", macIp->ip, macIp->mac );
            
        }
        addr = addr->next;
    }
}

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if_arp.h>

/* Delete an entry from the ARP cache. */
int delArpEntry(char *ip, char *dev) {
    struct arpreq req;
    struct sockaddr_in sa;
    int flags = 0;
    int err;
    int sockfd = 0;

    if (!ip)
        return -1;      // IP address was not informed.
        
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket");
        return(-1);
    }

    memset((char *) &req, 0, sizeof(req));

    sa.sin_addr.s_addr = inet_addr(ip);
    sa.sin_family = AF_INET;
    
    /* If a host has more than one address, use the correct one! */
    memcpy((char *) &req.arp_pa, (char *) &sa, sizeof (struct sockaddr_in));

    req.arp_flags = ATF_PERM;
    
    if (dev)                                // If device is not NULL
        strcpy(req.arp_dev, dev);           // Strictly removing only from dev device
    
    if (flags == 0)
        flags = 3;

    err = -1;

    /* Call the kernel. */
    if (flags & 2) {
        if ((err = ioctl(sockfd, SIOCDARP, &req) < 0)) {
            if (errno == ENXIO) {
                if (flags & 1)
                    goto nopub;
     //		printf(_("No ARP entry for %s\n"), host);
                return (-1);
            }
            perror("SIOCDARP(priv)");
            return (-1);
        }
    }
    if ((flags & 1) && (err)) {
nopub:
        req.arp_flags |= ATF_PUBL;
        if (ioctl(sockfd, SIOCDARP, &req) < 0) {
            if (errno == ENXIO) {
     //		printf(_("No ARP entry for %s\n"), host);
                return (-1);
            }
            perror("SIOCDARP(pub)");
            return (-1);
        }
    }
    return (0);
}
