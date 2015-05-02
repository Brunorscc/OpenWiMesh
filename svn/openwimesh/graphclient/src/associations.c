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

#include "associations.h"

static struct nl80211_state myNlState;

/***********************************************
    Accessory functions
************************************************/

int ieee80211_channel_to_frequency(int chan) {
    if (chan < 14)
        return 2407 + chan * 5;

    if (chan == 14)
        return 2484;

    /* FIXME: dot11ChannelStartingFactor (802.11-2007 17.3.8.3.2) */
    return (chan + 1000) * 5;
}

int ieee80211_frequency_to_channel(int freq) {
    if (freq == 2484)
        return 14;

    if (freq < 2484)
        return (freq - 2407) / 5;

    /* FIXME: dot11ChannelStartingFactor (802.11-2007 17.3.8.3.2) */
    if (freq < 45000)
        return freq / 5 - 1000;

    if (freq >= 58320 && freq <= 64800)
        return (freq - 56160) / 2160;

    return 0;
}

void mac_addr_n2a(char *mac_addr, unsigned char *arg) {
    int i, l;

    l = 0;
    for (i = 0; i < ETH_ALEN; i++) {
        if (i == 0) {
            sprintf(mac_addr + l, "%02x", arg[i]);
            l += 2;
        } else {
            sprintf(mac_addr + l, ":%02x", arg[i]);
            l += 3;
        }
    }
}

int mac_addr_a2n(unsigned char *mac_addr, char *arg) {
    int i;

    for (i = 0; i < ETH_ALEN; i++) {
        int temp;
        char *cp = strchr(arg, ':');
        if (cp) {
            *cp = 0;
            cp++;
        }
        if (sscanf(arg, "%x", &temp) != 1)
            return -1;
        if (temp < 0 || temp > 255)
            return -1;

        mac_addr[i] = temp;
        if (!cp)
            break;
        arg = cp;
    }
    
    if (i < ETH_ALEN - 1)
        return -1;

    return 0;
}


/*******************************************************
    NL80211 Linux Wireless subsystem functions
********************************************************/

int nl80211_init() {
    int err;

    myNlState.nl_sock = nl_socket_alloc();
    if (!myNlState.nl_sock) {
        printf("Failed to allocate netlink socket.\n");
        return -ENOMEM;
    }

    if (genl_connect(myNlState.nl_sock)) {
        printf("Failed to connect to generic netlink.\n");
        err = -ENOLINK;
        nl_socket_free(myNlState.nl_sock);
        return err;
    }

    myNlState.nl80211_id = genl_ctrl_resolve(myNlState.nl_sock, "nl80211");
    if (myNlState.nl80211_id < 0) {
        printf("nl80211 not found.\n");
        err = -ENOENT;
        nl_socket_free(myNlState.nl_sock);
        return err;
    }

    return 0;
}

void nl80211_cleanup() {

    nl_socket_free(myNlState.nl_sock);

}

static int handleError(struct sockaddr_nl *nla, struct nlmsgerr *err, void *arg) {
    int *ret = (int*) arg;
    *ret = err->error;
    return NL_STOP;
}

static int handleFinish(struct nl_msg *msg, void *arg) {
    int *ret = (int*) arg;
    *ret = 0;
    return NL_SKIP;
}

static int handleAck(struct nl_msg *msg, void *arg) {
    int *ret = (int*) arg;
    *ret = 0;
    return NL_STOP;
}

static int handleInterfaceStationInfo(struct nl_msg *msg, void *arg) {

    struct genlmsghdr *gnlh = (struct genlmsghdr *) nlmsg_data(nlmsg_hdr(msg));
    struct nlattr * tb_msg[NL80211_ATTR_MAX + 1];
    struct nlattr * stationInfo[NL80211_STA_INFO_MAX + 1];
    struct nlattr * txRateInfo[NL80211_RATE_INFO_MAX + 1];

    associationListTp * associations = arg;

#pragma GCC diagnostic push     // Saves current state
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
//#pragma GCC diagnostic pop     // Restores current state
    static struct nla_policy statisticsPolicy[NL80211_STA_INFO_MAX + 1] = {
        /* [__NL80211_STA_INFO_INVALID] =*/     {},
        /* [NL80211_STA_INFO_INACTIVE_TIME] =*/ {.type = NLA_U32},
        /* [NL80211_STA_INFO_RX_BYTES] =*/      {.type = NLA_U32},
        /* [NL80211_STA_INFO_TX_BYTES] =*/      {.type = NLA_U32},
        /* [NL80211_STA_INFO_LLID] =*/          {.type = NLA_U16},
        /* [NL80211_STA_INFO_PLID] =*/          {.type = NLA_U16},
        /* [NL80211_STA_INFO_PLINK_STATE] =*/   {.type = NLA_U8},
        /* [NL80211_STA_INFO_SIGNAL] =*/        {.type = NLA_U8},
        /* [NL80211_STA_INFO_TX_BITRATE] =*/    {.type = NLA_NESTED},
        /* [NL80211_STA_INFO_RX_PACKETS] =*/    {.type = NLA_U32},
        /* [NL80211_STA_INFO_TX_PACKETS] =*/    {.type = NLA_U32},
        /* NL80211_STA_INFO_TX_RETRIES] =*/     {.type = NLA_U32},
        /* NL80211_STA_INFO_TX_FAILED] =*/      {.type = NLA_U32},
        /* NL80211_STA_INFO_SIGNAL_AVG] =*/     {.type = NLA_U8},
        /* NL80211_STA_INFO_RX_BITRATE] =*/     {},
        /* NL80211_STA_INFO_BSS_PARAM] =*/      {},
        /* NL80211_STA_INFO_CONNECTED_TIME] =*/ {},
        /* NL80211_STA_INFO_STA_FLAGS] =*/      {.minlen = sizeof(struct nl80211_sta_flag_update)},
//        /* NL80211_STA_INFO_BEACON_LOSS] =*/    {},
//        /* NL80211_STA_INFO_T_OFFSET] =*/       {}
    };
#pragma GCC diagnostic pop     // Restores current state

    nla_parse(tb_msg, NL80211_ATTR_MAX, genlmsg_attrdata(gnlh, 0), genlmsg_attrlen(gnlh, 0), NULL);

    if (!tb_msg[NL80211_ATTR_STA_INFO]) {
        return NL_SKIP; // Missing station info
    }

    if (nla_parse_nested(stationInfo, NL80211_STA_INFO_MAX, tb_msg[NL80211_ATTR_STA_INFO], statisticsPolicy)) {
        return NL_SKIP; // Failed parsing station info nested attributes
    }

#pragma GCC diagnostic push     // Saves current state
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
//#pragma GCC diagnostic pop     // Restores current state
    static struct nla_policy ratePolicy[NL80211_RATE_INFO_MAX + 1] = {
            /*[__NL80211_RATE_INFO_INVALID] =*/     {},
            /*[NL80211_RATE_INFO_BITRATE] =*/       {.type = NLA_U16  },
            /*[NL80211_RATE_INFO_MCS] =*/           {.type = NLA_U8   },
            /*[NL80211_RATE_INFO_40_MHZ_WIDTH] =*/  {.type = NLA_FLAG },
            /*[NL80211_RATE_INFO_SHORT_GI] =*/      {.type = NLA_FLAG }
//            /*[NL80211_RATE_INFO_BITRATE32] =*/     {.type = NLA_U32  }
    };
#pragma GCC diagnostic pop     // Restores current state

    int rate = 0;
    double txRate = 0;
    short int txRateMCS = 0;
    bool channelWidth;
    kChannelGuardInterval guardInterval = kChannelGuardIntervalLong;    // The default is assigned.

    if (stationInfo[NL80211_STA_INFO_TX_BITRATE]) {
            if (nla_parse_nested(txRateInfo, NL80211_RATE_INFO_MAX, stationInfo[NL80211_STA_INFO_TX_BITRATE], ratePolicy)) {
                    // Failed to parse txRate information... move on
            }
            else {
          /*      if (txRateInfo[NL80211_RATE_INFO_BITRATE32])
                        rate = nla_get_u32(txRateInfo[NL80211_RATE_INFO_BITRATE32]);
                else */
                if (txRateInfo[NL80211_RATE_INFO_BITRATE])
                        rate = nla_get_u16(txRateInfo[NL80211_RATE_INFO_BITRATE]);
                if (rate > 0)
                        txRate = (double)rate/10;

                if (txRateInfo[NL80211_RATE_INFO_MCS])
                        txRateMCS =  nla_get_u8(txRateInfo[NL80211_RATE_INFO_MCS]);
                if (txRateInfo[NL80211_RATE_INFO_40_MHZ_WIDTH])
                    channelWidth = true;
                else
                    channelWidth = false;
                if (txRateInfo[NL80211_RATE_INFO_SHORT_GI])
                    guardInterval = kChannelGuardIntervalShort;
                else
                    guardInterval = kChannelGuardIntervalLong;
            }
    }

    int rxBytes = 0, txBytes = 0;
    int rxPackets = 0, txPackets = 0;
    if (stationInfo[NL80211_STA_INFO_RX_BYTES] && stationInfo[NL80211_STA_INFO_RX_PACKETS]) {
                rxBytes = nla_get_u32(stationInfo[NL80211_STA_INFO_RX_BYTES]);
                rxPackets = nla_get_u32(stationInfo[NL80211_STA_INFO_RX_PACKETS]);
    }
    if (stationInfo[NL80211_STA_INFO_TX_BYTES] && stationInfo[NL80211_STA_INFO_TX_PACKETS]) {
                txBytes = nla_get_u32(stationInfo[NL80211_STA_INFO_TX_BYTES]);
                txPackets = nla_get_u32(stationInfo[NL80211_STA_INFO_TX_PACKETS]);
    }

    double rssi = 0;
    if (stationInfo[NL80211_STA_INFO_SIGNAL])
                    rssi = (int8_t)nla_get_u8(stationInfo[NL80211_STA_INFO_SIGNAL]);

    int inactiveTime = -1;
    if (stationInfo[NL80211_STA_INFO_INACTIVE_TIME])
                    inactiveTime = nla_get_u32(stationInfo[NL80211_STA_INFO_INACTIVE_TIME]);

    char macAddr[18];
    bzero(macAddr,18);
    mac_addr_n2a(macAddr, nla_data(tb_msg[NL80211_ATTR_MAC]));

    // Won't add this association if:
    //"inactive time" is too high - associated node might be down
    //"SINR" stands for Signal to Interference Plus Noise Ratio
    //"SINR" is too low (less then -12 dB or a value passed as a parameter) - communication might be poor, so don include this association
    //"rssi" is too high: zero, for example, implies not obtained
    short int SINR = rssi - DEFAULT_NOISE_LEVEL;
    if (associations->noise)
        SINR = rssi - associations->noise;

    short int minimumSINR = 12;
    if (associations->minSINR)
        minimumSINR = associations->minSINR;

    if (inactiveTime > INACTIVE_TIME_MAX || SINR < minimumSINR || rssi > MAX_RSSI)
        return NL_SKIP;

    // If we continued it's because we are connected to this BSS, so let's get this information to the interface's attributes
    // The memory allocated here must be freed later!!!!!!
    associatedIBSSTp *ibss = malloc( sizeof(associatedIBSSTp));
    bzero(ibss,sizeof(associatedIBSSTp));
    if (!ibss)
        return NL_SKIP;

    // If in IBSS mode, then insert to a list of associated IBSSes
//    strcpy(ibss->ssid, ssid);
    strcpy(ibss->bssid, macAddr);
//    strcpy(ibss->countryCode, countryCode);
    ibss->rssi = rssi;
    ibss->txRate = txRate;
    ibss->htMCS = txRateMCS;
    ibss->guardInterval = guardInterval;
    ibss->rxBytes = rxBytes;
    ibss->txBytes = txBytes;

    // Adding to the chained list of associations
    // If the begin is NULL, define this as the beginning and end
    if (!associations->begin) {
        associations->begin = ibss;
        associations->end = ibss;
        associations->end->next = NULL;
    }
    else {
        // The next of the current end is the newly created
        associations->end->next = ibss;
        // The new end is the newly created
        associations->end = ibss;
        associations->end->next = NULL;
    }
    associations->count++;

    return NL_SKIP;
}

int getWirelessBSSInfo(char *wlan, associationListTp *associationsPt) {

    int sockErr = nl80211_init();
    if (sockErr < 0) {
        return -1;
    }
        
    associationsPt->noise = DEFAULT_NOISE_LEVEL;
        
    struct nl_cb *cb;
    struct nl_cb *s_cb;
    struct nl_msg *msg;
    int err;

    msg = nlmsg_alloc();
    if (!msg) {
        printf("failed to allocate netlink message.\n");
        nl80211_cleanup();
        return -1;
    }

    cb = nl_cb_alloc(NL_CB_DEFAULT);
    s_cb = nl_cb_alloc(NL_CB_DEFAULT);
    if (!cb || !s_cb) {
        printf("failed to allocate netlink callbacks.\n");
        nlmsg_free(msg);
        nl80211_cleanup();
        return -1;
    }

    unsigned short int flags = NLM_F_DUMP;
    int ifIndex;
    err = getIfIndex(wlan, &ifIndex);

    if (ifIndex < 0) {    // Valor invalido para interface logica.
        err = -1;
        goto nla_put_failure;
    }
    
    genlmsg_put(msg, 0, 0, myNlState.nl80211_id, 0, flags, NL80211_CMD_GET_STATION, 0);
    NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, ifIndex);

    nl_cb_set(cb, NL_CB_VALID, NL_CB_CUSTOM, handleInterfaceStationInfo, associationsPt);

    nl_socket_set_cb(myNlState.nl_sock, s_cb);

    err = nl_send_auto_complete(myNlState.nl_sock, msg);

    if (err < 0) {
        nl_cb_put(cb);
        nlmsg_free(msg);
        nl80211_cleanup();
        return err;
    }

    // Cleaning up communication bus ...
    err = 1;

    nl_cb_err(cb, NL_CB_CUSTOM, handleError, &err);
    nl_cb_set(cb, NL_CB_FINISH, NL_CB_CUSTOM, handleFinish, &err);
    nl_cb_set(cb, NL_CB_ACK, NL_CB_CUSTOM, handleAck, &err);

    while (err > 0)
        nl_recvmsgs(myNlState.nl_sock, cb);
    
    // Se passar por aqui o comando funcionou e a lista de associados está preenchida, basta enviar pacote UDP.
    
nla_put_failure:

    nl_cb_put(cb);
    nlmsg_free(msg);
    nl80211_cleanup();
    return err;
}

static int handleSurvey(struct nl_msg *msg, void *arg)
 {
     struct nlattr *tb[NL80211_ATTR_MAX + 1];
     struct genlmsghdr *gnlh = nlmsg_data(nlmsg_hdr(msg));
     struct nlattr *sinfo[NL80211_SURVEY_INFO_MAX + 1];
         associationListTp * associationsPt = arg;

     static struct nla_policy surveyPolicy[NL80211_SURVEY_INFO_MAX + 1] = {
         [NL80211_SURVEY_INFO_FREQUENCY] = { .type = NLA_U32 },
         [NL80211_SURVEY_INFO_NOISE] = { .type = NLA_U8 },
     };

     nla_parse(tb, NL80211_ATTR_MAX, genlmsg_attrdata(gnlh, 0),
           genlmsg_attrlen(gnlh, 0), NULL);

     if (!tb[NL80211_ATTR_SURVEY_INFO]) {
         printf("Survey data is missing!\n");
         return NL_SKIP;
     }

     if (nla_parse_nested(sinfo, NL80211_SURVEY_INFO_MAX,
                  tb[NL80211_ATTR_SURVEY_INFO],
                  surveyPolicy)) {
         printf("Failed to parse nested attributes!\n");
         return NL_SKIP;
     }

     if (sinfo[NL80211_SURVEY_INFO_FREQUENCY]) {
             int channelNumber = ieee80211_frequency_to_channel(nla_get_u32(sinfo[NL80211_SURVEY_INFO_FREQUENCY]));
             bool inUse = sinfo[NL80211_SURVEY_INFO_IN_USE];
             if (inUse) {
                 associationsPt->channelNumber = channelNumber;
                 if (sinfo[NL80211_SURVEY_INFO_NOISE]) {
                     associationsPt->noise = (int8_t)nla_get_u8(sinfo[NL80211_SURVEY_INFO_NOISE]);
                     if (associationsPt->noise == 0 || associationsPt->noise < -100)
                         associationsPt->noise = DEFAULT_NOISE_LEVEL;
                 }

                 unsigned long long channelTime;
                 if (sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME]) {
                     channelTime = (unsigned long long)nla_get_u64(sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME]);
                     associationsPt->channelTime = channelTime;
                 }
                 else {
                     associationsPt->channelTime = -1;
                 }

 /*
                 (unsigned long long)nla_get_u64(sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME_BUSY]));
                 (unsigned long long)nla_get_u64(sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME_EXT_BUSY]));
                 (unsigned long long)nla_get_u64(sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME_RX]));
                 (unsigned long long)nla_get_u64(sinfo[NL80211_SURVEY_INFO_CHANNEL_TIME_TX]));
  */
             }
         }
     return NL_SKIP;
 }

int getChannelSurvey(char *wlan, associationListTp *associationsPt) {

    int sockErr = nl80211_init();
    if (sockErr < 0) {
        return -1;
    }

    struct nl_cb *cb;
    struct nl_cb *s_cb;
    struct nl_msg *msg;
    int err;

    msg = nlmsg_alloc();
    if (!msg) {
        printf("failed to allocate netlink message.\n");
        nl80211_cleanup();
        return -1;
    }

    cb = nl_cb_alloc(NL_CB_DEFAULT);
    s_cb = nl_cb_alloc(NL_CB_DEFAULT);
    if (!cb || !s_cb) {
        printf("failed to allocate netlink callbacks.\n");
        nlmsg_free(msg);
        nl80211_cleanup();
        return -1;
    }

    unsigned short int flags = NLM_F_DUMP;
    int ifIndex;
    err = getIfIndex(wlan, &ifIndex);

    if (ifIndex < 0) {    // Valor invalido para interface logica.
        err = -1;
        goto nla_put_failure;
    }

    genlmsg_put(msg, 0, 0, myNlState.nl80211_id, 0, flags, NL80211_CMD_GET_SURVEY, 0);
    NLA_PUT_U32(msg, NL80211_ATTR_IFINDEX, ifIndex);

    nl_cb_set(cb, NL_CB_VALID, NL_CB_CUSTOM, handleSurvey, associationsPt);

    nl_socket_set_cb(myNlState.nl_sock, s_cb);

    err = nl_send_auto_complete(myNlState.nl_sock, msg);

    if (err < 0) {
        nl_cb_put(cb);
        nlmsg_free(msg);
        nl80211_cleanup();
        return err;
    }

    // Cleaning up communication bus ...
    err = 1;

    nl_cb_err(cb, NL_CB_CUSTOM, handleError, &err);
    nl_cb_set(cb, NL_CB_FINISH, NL_CB_CUSTOM, handleFinish, &err);
    nl_cb_set(cb, NL_CB_ACK, NL_CB_CUSTOM, handleAck, &err);

    while (err > 0)
        nl_recvmsgs(myNlState.nl_sock, cb);

nla_put_failure:

    nl_cb_put(cb);
    nlmsg_free(msg);
    nl80211_cleanup();
    return err;
}

/*
 UDP Message sending ...
*/
int sendUDPMessage(char *wlan,
                   associationListTp *associationsPt,
                   char *serverIPPort,
                   unsigned long int totalBytes,
                   bool emulMode) {
    // Code
   short mLen;
   char *message=NULL, *tmp=NULL;
   char buf[UDP_MESSAGE_PART];
//   char macAddr[18];
//   char ipAddr[16];
   char dstIpAddr[16];
   unsigned int dstUdpPort = UDP_PORT;  // Assuming 1111 as the default.
   char *wlanIntf;
   double SINR, projSpeed;
   
   // Wlan logical interface name
   wlanIntf = wlan;
   
 /*  i = getIfMacAddr(argv[6], macAddr);
   if (i<0) {
       printf("Could not obtain Mac Address from %s\n", argv[6]);
       return -1;
   }
   i = getIfIPAddr(argv[6], ipAddr);
   if (i<0) {
       printf("Could not obtain IP Address from %s\n", argv[6]);
       return -1;
   } */

//   sprintf(message, "%s|%s;", ipAddr, macAddr);
//   sprintf(message, "%s;", wlanIntf);   // Message Header
   
   char *serverIpPort = strtok(serverIPPort, ":");  // Tries to find a ":" separator in string in the form "IP:PORT"
   if (serverIpPort) {
       strcpy(dstIpAddr, serverIpPort);             // Copies IP Address
       serverIpPort = strtok(NULL, ":");            // Next token
       if (serverIpPort)
           dstUdpPort = atoi(serverIpPort);         // Convert UDP port string to an integer
       else
           dstUdpPort = UDP_PORT;                   // If no port is provided, use default.
   }

   char format[] = "%s|%s|%02.0f|%li|%li|%.1f|%.1f;";
   associatedIBSSTp *assocItem = associationsPt->begin;
   while (assocItem) {
       bzero(buf, UDP_MESSAGE_PART);
       if (!assocItem->next) {                  // Last associated IBSS, so no ";" at the end.
           int fLen = strlen(format);
           format[fLen-1] = 0;                  // Erases the char ";" in sprintf's formating string
       }
       SINR = assocItem->rssi - associationsPt->noise;

       if (!emulMode)
            projSpeed = projectedSpeedBasedOnSINR(SINR, assocItem->htMCS, 0, 1, assocItem->guardInterval);
       else
            projSpeed = assocItem->txRate;

       sprintf(buf, format,
               wlanIntf,                        // wlan interface name
               assocItem->bssid,                // BSSID of associated node
               assocItem->rssi,                 // RSSI of associated node in this node
               assocItem->rxBytes + \
               assocItem->txBytes,              // tx+rx bytes in this association only
               totalBytes,                      // tx+rx bytes in all associations of this node's
               assocItem->txRate,               //current operational speed
               projSpeed);                      // predicted speed

       if (message)
           mLen = strlen(message) + strlen(buf);
       else
           mLen = strlen(buf);
       tmp = malloc(mLen + 1);
       *tmp = '\0';
       if (message) {
            strcpy(tmp, message);
            free(message);
       }
       strcat(tmp, buf);
       message = tmp;

       // Limiting the message body is an attempt to fit
       // the message in an UDP packet less them 1000 bytes.
       if (mLen > UDP_PKT_PAYLOAD_MAX) {
           // Sends this partial message in an UDP packet.
           // The rest of the message will be sent in other UDP packets.
           sendUDPMsgPart(dstIpAddr, dstUdpPort, message);
           free(message);
           message = NULL;
       }
       assocItem = assocItem->next;
   }

   if (message) {
       // Sends the final message Part.
       sendUDPMsgPart(dstIpAddr, dstUdpPort, message);
   }

   free(message);
    
   return 0;
}

/*
 UDP Message Part sending. Message body limited to 900 bytes.
*/
int sendUDPMsgPart(char *dstIpAddr,
                   short dstUdpPort,
                   char *message) {

    int sock, i;
    unsigned int length;
    struct sockaddr_in server; //, from;

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("Could not open UDP socket.\n");
        return -1;
    }

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(dstIpAddr);
    server.sin_port = htons(dstUdpPort);
    length = sizeof(struct sockaddr_in);

    //////////////////////////////////////////////////
    // Just for verification purposes. Comment later.
    time_t now = time(NULL);
    printf("--> Time:\n%s--> UDPMesg:\n%s\n", asctime(localtime(&now)), message);
    fflush(stdout);  // To print immediately
    //////////////////////////////////////////////////

    i = sendto(sock, message, strlen(message), 0, (const struct sockaddr *)&server, length);
    if (i < 0) {
        printf("Failed to send UDP message Part.\n");
        return -1;
    }
    close(sock);

    return 0;
}


// Should pass an initialized memory area with 18 bytes at least for MacAddr return
int getIfMacAddr(const char *ifName, char *ifMacAddr) {

    struct ifreq s;
    int err;
    int fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);

    strcpy(s.ifr_name, ifName);
    if ((err = ioctl(fd, SIOCGIFHWADDR, &s)) < 0) {
        close(fd);
        return -1;
    }
    sprintf(ifMacAddr, "%02x:%02x:%02x:%02x:%02x:%02x",
            (uint8_t)s.ifr_hwaddr.sa_data[0],
            (uint8_t)s.ifr_hwaddr.sa_data[1],
            (uint8_t)s.ifr_hwaddr.sa_data[2],
            (uint8_t)s.ifr_hwaddr.sa_data[3],
            (uint8_t)s.ifr_hwaddr.sa_data[4],
            (uint8_t)s.ifr_hwaddr.sa_data[5]
            );
    close(fd);
    return 0;
}

int getIfIndex(const char *ifName, int *ifIndex) {

    struct ifreq s;
    int err;
    int fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);

    strcpy(s.ifr_name, ifName);
    if ((err = ioctl(fd, SIOCGIFINDEX, &s)) < 0) {
        close(fd);
        return -1;
    }
    *ifIndex = s.ifr_ifindex;
    
    close(fd);
    return 0;
}

// Should pass an initialized memory area with 16 bytes at least for IPAddr return
int getIfIPAddr(const char *ifName, char *ipAddr) {

    struct ifreq s;
    int err;
    int fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);

    strcpy(s.ifr_name, ifName);
    if ((err = ioctl(fd, SIOCGIFADDR, &s)) < 0) {
        close(fd);
        return -1;
    }

    struct sockaddr_in *ipAddrIn = (struct sockaddr_in *)&(s.ifr_addr);
    strcpy(ipAddr, inet_ntoa(ipAddrIn->sin_addr));

    close(fd);
    return 0;
}

double projectedSpeedBasedOnSINR(double SINR,
                                  short int MCSValue,
                                  short int HTMode,     // HT20 ou HT40 ou non-HT
                                  short int spatialStreams,
                                  short int guardInterval)
{
    double speed;

    if (SINR >= dot11A_54MbpsSNRThreshold)
        speed = 54;
    else if (SINR >= dot11A_48MbpsSNRThreshold)
        speed = 48;
    else if (SINR >= dot11A_36MbpsSNRThreshold)
        speed = 36;
    else if (SINR >= dot11A_24MbpsSNRThreshold)
        speed = 24;
    else if (SINR >= dot11A_18MbpsSNRThreshold)
        speed = 18;
    else if (SINR >= dot11A_12MbpsSNRThreshold)
        speed = 12;
    else if (SINR >= dot11A_06MbpsSNRThreshold)
        speed = 6;
    else if (SINR >= dot11B_11MbpsSNRThreshold)
        speed = 11;
    else if (SINR >= dot11B_05MbpsSNRThreshold)
        speed = 5.5;
//    else if (SINR >= dot11B_02MbpsSNRThreshold) // It is so near that it's not worth consider
//        speed = 2;
    else if (SINR >= dot11B_01MbpsSNRThreshold)
        speed = 1;
    else
        speed = 1; // If it is associated but with a very weak signal, only 1 Mbps will do.

    return speed;
 }

// Reads a file "neighbors" in local directory with all association information
int getEmulatedAssociationList(associationListTp *associationsPt) {

    // Association info is in each line of the neighbors file.
    char format[] = "%[^|] | %lf | %lf %*[;] %*[\n]";
/*
    associationsPt->ibssList[i]->bssid,      // BSSID of associated node (will have to define one based on the \
                                            node id. It is being defined the same way when the node is created on CORE).
    associationsPt->ibssList[i]->rssi,       // RSSI of associated node in this node (we will provide)
    totalBytes,                              // tx+rx bytes in all associations of this node (graphClient will get from "eth0")
    associationsPt->ibssList[i]->txRate,     // current operational speed (we will provide)
*/

//    char sep[5];
    FILE *neighFile = fopen("neighbors", "r");
    if (!neighFile) {
        printf("Could not open neighbors file.\n");
        return -1;
    }
    int readItems;
    do {
        associatedIBSSTp *ibss = malloc(sizeof (associatedIBSSTp));
        bzero(ibss, sizeof (associatedIBSSTp));
        if (!ibss) {
            printf("No memory available when reading emulated neighbors info.\n");
            return -1;          // No memory available.
        }

        readItems = fscanf(neighFile, format,
                ibss->bssid,
                &(ibss->rssi),
                &(ibss->txRate));

        if (readItems >= 0) {
            // If the begin is NULL, define this as the beginning and end
            if (!associationsPt->begin) {
                associationsPt->begin = ibss;
                associationsPt->end = ibss;
                associationsPt->end->next = NULL;
            }
            else {
                // The next of the current end is the newly created
                associationsPt->end->next = ibss;
                // The new end is the newly created
                associationsPt->end = ibss;
                associationsPt->end->next = NULL;
            }
            associationsPt->count++;
        }
    }    
    while (readItems>0);
    
    return 0;
}

// Reads bytes transported by the emulated wireless interface via "ifconfig".
int getEmulatedWiFiIntfTotalBytes(char* ifName, long long unsigned int *totalBytes) {

    FILE *f;
    char cmd[50];
    int bufSize = 200;
    char buf[bufSize];
    long long unsigned int rxBytes, txBytes;
    int read;

    sprintf(cmd, "ifconfig %s", ifName);
    f = popen(cmd, "r");
    if (!f) {
        printf("Could not execute \"ifconfig\" command\n");
        return -1;
    }
    while ( fgets(buf, bufSize, f) != NULL) {
// Sample string ...
//"          RX bytes:155763204 (155.7 MB)  TX bytes:23611393 (23.6 MB)"
        read = sscanf(buf," RX bytes: %llu %*s TX bytes: %llu %*s",
                          &rxBytes, &txBytes);
        if (read > 0) {
            //printf("Rx = %llu, Tx = %llu\n", rxBytes, txBytes);
            *totalBytes = rxBytes + txBytes;
            break;
        }
    }
    pclose(f);
    return 0;
}

// Checks the openflow switch connection status. If connection status has changed,
//adjust interface packet-in configuration.
// This routine is considering that only one interface is being used on the bridge interface ofSwName
// Returns the current connection status
int checkOFSwitchConnStatus(bool lastConnStatus, char* ofSwName, char *macVlanIntf) {

    FILE *f;
    char cmd1[] = "ovs-vsctl -t 1 show 2> /dev/null | grep is_connected";
    char cmd2[] = "ovs-ofctl -t 1 mod-port %s %s %s";
    int bufSize = 200;
    char buf[bufSize];
    bool newConnectionStatus = false;

    // Let's check if is connected to the controller
    f = popen(cmd1, "r");
    if (!f) {
        printf("Could not execute \"%s\" command\n", cmd1);
        fflush(stdout);  // To print immediately
        return -1;
    }
    while ( fgets(buf, bufSize, f) != NULL) {
    // Sample string ...
    //"          is_connected: true"
        if ( strtok(buf,"true") )
            newConnectionStatus = true;
    }
    pclose(f);

    // TESTING ONLY. COMMENT LATER !!!
    //newConnectionStatus = true;

    // If the connection status has changes since last check, adjust pkt_in authorization
    if (lastConnStatus != newConnectionStatus) {
        int pkt_in_len = 20;
        char pkt_in[pkt_in_len];
        if (newConnectionStatus)
            strncpy(pkt_in, "packet-in", pkt_in_len);
        else
            strncpy(pkt_in, "no-packet-in", pkt_in_len);
        sprintf(buf, cmd2, ofSwName, macVlanIntf, pkt_in);
        //printf(buf);
        //printf("\n");
        f = popen(buf, "r");
        if (!f) {
            printf("Could not execute \"%s\" command\n", buf);
            fflush(stdout);  // To print immediately
            return -1;
        }
        else {
            time_t now = time(NULL);
            printf("--> Time:\n%s", asctime(localtime(&now)));
            if (newConnectionStatus) {
                printf("Openflow Switch Connection is UP. Enabling packet-ins...\n");
            }
            else {
                printf("Openflow Switch Connection is DOWN. Disabling packet-ins...\n");
            }
            fflush(stdout);  // To print immediately
        }
        pclose(f);
    }
    return newConnectionStatus;
}

// This routine is considering that only one interface is being used on the bridge interface ofSwName
int getIntfOnOFSwitch(char* ofSwName, char **intfOnOFSw) {

    char cmd3[] = "ovs-vsctl -t 1 list-ports %s";
    FILE *f;
    int bufSize = UDP_MESSAGE_PART;
    char buf[bufSize];

    // First let's obtain the interface name on the informed bridge interface
    sprintf(buf, cmd3, ofSwName);
    f = popen(buf, "r");
    if (!f) {
        printf("Could not execute \"%s\" command\n", buf);
        return -1;
    }
    // Reads only the first line, which is the first and only interface name
    // Sample string ...
    //"mac0"
    fgets(*intfOnOFSw, INTERFACE_NAME_MAX, f);

    // Now removing any Carriage Return and Line Feed
    short macVlanIntfLen = strlen(*intfOnOFSw);
    short i;
    char *p = *intfOnOFSw;
    for (i=0; i<macVlanIntfLen; i++) {
        if (*p == '\r' || *p == '\n')
            *p = ' ';
        p++;
    }
    pclose(f);
    return 0;
}

void freeAssocListMem(associationListTp *assocList) {
    associatedIBSSTp *assocItem, *tmp;
    assocItem = assocList->begin;
    while (assocItem) {
        tmp = assocItem->next;
        free(assocItem);
        assocItem = tmp;
    }
}
