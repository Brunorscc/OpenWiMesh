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

#ifndef ASSOCIATIONS_H
#define	ASSOCIATIONS_H
/*
#ifdef	__cplusplus
extern "C" {
#endif
*/
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <net/if.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdbool.h>
#include <netlink/netlink.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/family.h>
#include <netlink/genl/ctrl.h>
#include <endian.h>

#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <linux/nl80211.h>
#include <time.h>

#define ETH_ALEN             6      // The ethernet address lenght in binary format
#define MAX_SSID_LEN         50     // Char limit for an SSID
#define UDP_PORT             1111   // UDP Port used to send a message to OpenFlow Controller. TODO: mudar formato do parametro de entrada para IP:Porta
#define UDP_MESSAGE_PART     90     // Each piece of the UDP message
#define UDP_PKT_PAYLOAD_MAX  10000  // If the UDP message payload is bigger then this, more than one packet will be sent
#define DEFAULT_NOISE_LEVEL -90     // Default noise level set to -90 if no noise info available
#define INACTIVE_TIME_MAX    30500  // Maximum amount of time an association can be inactive before being omited from the associations list
#define MAX_RSSI            -10     // Maximum value in dBm that a RSSI can have. If bigger, association will be omited from the list
#define INTERFACE_NAME_MAX   60     // Maximum lenght for an interface name

typedef enum kChannelGuardInterval {
    kChannelGuardIntervalLong,      // 800 nSeconds. Default.
    kChannelGuardIntervalShort      // 400 nSeconds
} kChannelGuardInterval;

struct nl80211_state {
    struct nl_sock *nl_sock;
    int nl80211_id;
};

typedef struct associatedIBSS {
    char bssid[18];
//    char ssid[MAX_SSID_LEN];
//    char countryCode[4];
    double rssi;
    double txRate;
    short int htMCS;
    kChannelGuardInterval guardInterval;
    long int rxBytes;
    long int txBytes;
    struct associatedIBSS *next;
} associatedIBSSTp;

typedef struct associationList {
    short int count;                    // Associations total
    short int channelNumber;            // Channel number
    short int noise;                    // Range from -128 to 127, typically negative
    short int minSINR;                  // Minimum SINR informed at command line
    unsigned long long channelTime;     // Channel occupied time. If negative, no info available
    struct associatedIBSS *begin;
    struct associatedIBSS *end;
} associationListTp;

void freeAssocListMem(associationListTp *assocList);

void mac_addr_n2a(char *mac_addr, unsigned char *arg);
int mac_addr_a2n(unsigned char *mac_addr, char *arg);
int ieee80211_channel_to_frequency(int chan);
int ieee80211_frequency_to_channel(int freq);

//static int handleInterfaceStationInfo(struct nl_msg *msg, void *arg);
//static int handleSurvey(struct nl_msg *msg, void *arg);
int getIfMacAddr(const char *ifName, char *ifMacAddr);
int getIfIndex(const char *ifName, int *ifIndex);
int getIfIPAddr(const char *ifName, char *ipAddr);
int getChannelSurvey(char *wlan, associationListTp *associationsPt);
int getWirelessBSSInfo(char *wlan, associationListTp *associationsPt);
int sendUDPMessage(char *wlan, associationListTp *associationsPt, 
                   char *serverIPPort, unsigned long int totalBytes, bool emulMode);
int sendUDPMsgPart(char *dstIpAddr,
                   short dstUdpPort,
                   char *message);
int getEmulatedAssociationList(associationListTp *associationsPt);
int getEmulatedWiFiIntfTotalBytes(char* ifName, long long unsigned int *totalBytes);
int checkOFSwitchConnStatus(bool isConnected, char* ofSwName, char *macVlanIntf);
int getIntfOnOFSwitch(char* ofSwName, char **macVlanIntf);

// This table came from Picture 8 from paper "Effect of adjacent-channel interference in IEEE 802.11 WLANs" de Villegas et. all
#define dot11A_54MbpsSNRThreshold 22.0  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_48MbpsSNRThreshold 20.5  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_36MbpsSNRThreshold 15.5  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_24MbpsSNRThreshold 12.5  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_18MbpsSNRThreshold  9.0  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_12MbpsSNRThreshold  6.0  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11A_06MbpsSNRThreshold  3.0  // Minimum dBm that allows this MCS (modulation and code scheme)

// This table came from Picture 2 from paper "A Throughput Optimization and Transmitter Power Saving Algorithm For IEEE 802.11b Links" de Mo and Bostian
#define dot11B_11MbpsSNRThreshold 19.5  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11B_05MbpsSNRThreshold 15.0  // Minimum dBm that allows this MCS (modulation and code scheme)
#define dot11B_02MbpsSNRThreshold 14.5  // Minimum dBm that allows this MCS (modulation and code scheme) - Não usar pois não vale a pena comparado com anterior
#define dot11B_01MbpsSNRThreshold 10.0  // Minimum dBm that allows this MCS (modulation and code scheme)

double projectedSpeedBasedOnSINR(double SINR,
                                  short int MCSValue,
                                  short int HTMode,     // HT20 ou HT40 ou non-HT
                                  short int spatialStreams,
                                  short int guardInterval);

/*    
#ifdef	__cplusplus
}
#endif
*/
#endif	/* ASSOCIATIONS_H */

