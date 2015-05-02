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

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include "associations.h"
#include "arpInfo.h"
#include "paramprocess.h"

#define SHORT_WAIT_TIME         100000      // 100 milisseconds
#define LONG_WAIT_TIME          1000000     // 1 second
#define UDP_MSG_TIME_INTERVAL   5           // In seconds

// Executes GraphClient's main process with options

int process(bool delArp,
        bool sendUDPMsg,
        associationListTp *assocPt,
        struct chainedList *arpTablePt,
        char *wlan,
        char *br,
        char *serverIPPort,
        bool emulationMode) {

    unsigned long long int totalBytes = 0;

    /////////////////////////////////////////////////////
    // If authorized to clean the ARP table (mobility function, disabled by the
    //"-arp" command line parameter)
    short retErr = 0;
//    if (delArp) {
        // Defining arp table variable and getting its contents for specified "bridge" interface
//        initArpTableList(arpTablePt);
//        retErr = getArpForIntf(br, arpTablePt);
        //printArpTable(&arpTable);
//    }
    /////////////////////////////////////////////////////

    /////////////////////////////////////////////////////
    // Node associations processing ...
    //
    // Get associations list process
    assocPt->count = 0;
    assocPt->noise = 0;
    assocPt->minSINR = 0;   // This is being loaded before but it is cleared HERE
    //so it is not in effect.

    // Initializes the association list pointers with NULL
    //to inform that the list is empty.
    assocPt->begin = NULL;
    assocPt->end = NULL;

    // If it is not to clear ARP table and will not send UDP message,
    //there is no need to read the assocations
    if (delArp || sendUDPMsg) {

        if (!emulationMode) {
            // Gets noise level in the wireless interface
            retErr = getChannelSurvey(wlan, assocPt);

            if (retErr >= 0) {
                // Get the list of associated wireless nodes
                retErr = getWirelessBSSInfo(wlan, assocPt);

                // Computes the total bytes transported by the wireless interface
                associatedIBSSTp *assocItem = assocPt->begin;
                while (assocItem) {
                    totalBytes += assocItem->txBytes;
                    totalBytes += assocItem->rxBytes;
                    assocItem = assocItem->next;
                }
            }
        }
        else {
            // Reads a file "neighbors" in local directory with all association information
            retErr = getEmulatedAssociationList(assocPt);
            // Reads bytes transported by the emulated wireless interface using IOCTL.
            if (retErr >= 0 && sendUDPMsg)
                // Read the total transferred bytes (sum of in and out) from the supplied interface
                retErr = getEmulatedWiFiIntfTotalBytes(wlan, &totalBytes);
        }

        if (retErr >= 0 && sendUDPMsg)
            retErr = sendUDPMessage(wlan, assocPt, serverIPPort, totalBytes, emulationMode);

    }
    /////////////////////////////////////////////////////

    /////////////////////////////////////////////////////
    // Continuation of the ARP cleaning process, again if athorized to do it ...
//    if (delArp) {
//        // Remove arp cache entries if not at reach anymore (may be down or moved)
//        delArpEntriesIfNotAtReach(arpTablePt, assocPt, br);
//        // Frees memory for arp manipulation
//        clearChainedList(arpTablePt);
//    }
    /////////////////////////////////////////////////////

    // Frees memory allocated for associations structs
    freeAssocListMem(assocPt);

    return retErr;
}

// Returns the number of defined params
void defineParams(argvParamList **pList) {
    // First
    defParam(pList, "-w", NULL, false, true,
             "-w <logical wireless interface name[:minimum SINR to association]>");
    // Second
    defParam(pList, "-o", NULL, false, true,
             "-o <open flow controller IP[:Port address]>");
    // Third
    defParam(pList, "-b", NULL, false, true,
             "-b <open flow local switch bridge interface>");
    // Fourth
    defParam(pList, NULL, "-arp", true, false,
             "[-arp] -> Key to disable arp cache entries removal if not associated to them");
    // Fifth
    defParam(pList, "-E", NULL, true, false,
             "[-E] or [--emulation] -> Keys to operate in Emulation mode");
    return;
}

int main(int argc, char **argv) {

    // Changed to "Manually" defining version
    char version[] = "v0.6";
    unsigned int build = 1;

    // Data structure for holding command line parameters info
    argvParamList *p = NULL;        // Must be initialized with NULL
    defineParams(&p);
    short err = parseParams(p, argc, argv);
    if (err<0) {
        printSyntax(p, version, build);
        // Free memory from params
        freeParamMem(p);
        return -1;
    }
    // Checking if is to disable arp cache removal function.
    bool removeArp = true;
    if (getParamState(p, NULL, "-arp"))
        removeArp = false;

    // Check if it should operate in Emulation Mode
    bool emulationMode = false;
    if (getParamState(p, "-E", "--emulation"))
        emulationMode = true;

    // Define data structure for associations info, arpTable info
    associationListTp associations;
    struct chainedList arpTable;

    // Obtain WLAN interface parameter
    char *wlanStr = getParamValue(p, "-w", NULL);
    // This minimum SINR level is not in use anymore
    // It will not be taken into account if informed
    char *wlanSINR = strtok(wlanStr, ":");  // Tries to find a ":" separator in string in the form "wlan:SINR"
    strcpy(wlanStr, wlanSINR);              // Copies IP Address
    wlanSINR = strtok(NULL, ":");           // Next token
    if (wlanSINR) {
        // Converts minimum SINR level string to an integer
        associations.minSINR = atoi(wlanSINR);
        // Copying the cleared wlan string back to argv.
        //strcpy(&p[0].value, wlanStr);
    }

    // Obtain Openflow Controller info and Bridge Interface name
    char *ofCtrl = getParamValue(p, "-o", NULL);
    char *brdIntf = getParamValue(p, "-b", NULL);

    // Obtain interface name connected to the Openflow switch bridge, to control its packet-in attribute
    // It might be a MacVlanInterface (Emulation) or a regular wireless interface
    char *intfOnOFSw = malloc(INTERFACE_NAME_MAX);
    err = getIntfOnOFSwitch(brdIntf, &intfOnOFSw);
    if (err < 0) {
        printf("Could not find any interface on the Openflow Switch Bridge. Cannot continue this way. Aborting ...\n");
        free(intfOnOFSw);
        freeParamMem(p);
    }

    /////////////////////////////////////////////////////
    // Initiating processing ...

    bool ofSwConnStatus = false;    // Holds the openflow switch connection status
    int waitTime = SHORT_WAIT_TIME;
    time_t udpMsgCtrlTime = time(NULL);

    while (true) {
        /////////////////////////////////////////////////////
        // Checks if it has happened a connection status change on the openflow switch and adjusts the "packet-in"
        //parameter on the wireless interface. If return value is < 0, then an error ocurred.
        // Any further processing will only be executed if the node's switch is connected to an Openflow controller
        bool lastOfSwConnStatus = ofSwConnStatus;
        short retConn = checkOFSwitchConnStatus(lastOfSwConnStatus, brdIntf, intfOnOFSw);

        /////////////////////////////
        // DEBUGGING ONLY, COMMENT LATER!!!
        // Forcing connection status to true to test the logic
        //retConn = 1;
        /////////////////////////////

        if (retConn == 0) {
            ofSwConnStatus = false;
            waitTime = SHORT_WAIT_TIME;
        }
        else if (retConn > 0) {
            ofSwConnStatus = true;
            waitTime = LONG_WAIT_TIME;
        }
        /////////////////////////////////////////////////////

        /////////////////////////////////////////////////////
        // Deciding if we should send an UDP message now...
        //
        // Will be true if switch is connected
        // AND
        // elapsed time since last UDP message is greater then interval constant
        // OR
        // If we have just connected to the controller
        bool sendUDPMsg = ( ofSwConnStatus &&
                            (difftime(time(NULL), udpMsgCtrlTime) >= UDP_MSG_TIME_INTERVAL) )
                          ||
                          (lastOfSwConnStatus==false && ofSwConnStatus==true);

        // DEBUG ONLY. COMMENT LATER!!!
        //if (sendUDPMsg)
        //    printf ("Should send UDP msg\n");
        //printf ("Processing ...\n");

        // Process associations ...
        err = process(removeArp, sendUDPMsg, &associations, &arpTable,
                       wlanStr, brdIntf, ofCtrl,
                       emulationMode);

        // Re-initialize the time of last UDP message sent
        if (sendUDPMsg) {
            udpMsgCtrlTime = time(NULL);
        }

        // Wait time between proccessings ...
        usleep(waitTime);
    }

    freeParamMem(p);
    return err;
}
