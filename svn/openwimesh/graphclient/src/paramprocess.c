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
#include "paramprocess.h"

// Adds to the end of the chained list and return the newly added
argvParamItem *addParam(argvParamList **pList) {
    // If this will be the first in the chain...
    if (!*pList) {
        *pList = malloc(sizeof(argvParamList));
        (*pList)->start = malloc(sizeof(argvParamItem));
        (*pList)->start->next = NULL;    // Define the end of the chain
        (*pList)->end = (*pList)->start;   // This is the end
    }
    // else just add to the chain
    else {
        argvParamItem *newParam = malloc(sizeof(argvParamItem));
        (*pList)->end->next = newParam;
        (*pList)->end = newParam;
        (*pList)->end->next = NULL;
    }
    return (*pList)->end;
}

void defParam(argvParamList **pList,
              char *key,
              char *eKey,
              bool boolVal,
              bool req,
              char *hMsg) {
    argvParamItem *p = addParam(pList);
    p->boolVal = boolVal;
    p->req = req;
    if (key)
        strncpy(p->key, key, 3);    // Copies also \0
    else
        p->key[0] = '\0';           // Forces as empty string
    if (eKey) {
        p->extKey = malloc(strlen(eKey)+1);
        strncpy(p->extKey, eKey, strlen(eKey)+1);
    }
    else
        p->extKey = NULL;
    if (hMsg) {
        p->helpMsg = malloc(strlen(hMsg)+1);
        strncpy(p->helpMsg, hMsg, strlen(hMsg)+1);  // Copies also \0
    }
    else
        p->helpMsg = NULL;
    p->value = NULL;            // Clears it, so we know that if it is not NULL has to be freed later
}

void printSyntax(argvParamList *pList, char *ver, int build) {
    printf("\nVersion: %s - Build: %u\nProgram syntax:\nGraphClient \\\n", ver, build);
    argvParamItem *it = pList->start;
    while (it) {
/*        if (p[i]->key) {
            printf("%s ", p[i]->key);
            if (p[i]->extKey)
                printf("or %s ", p[i]->extKey);
        }
        else {
            printf("%s ", p[i]->extKey);
        } */
        if (it->next)
            printf("%s \\\n", it->helpMsg);
        else
            printf("%s\n", it->helpMsg);
        it = it->next;
    }
}

void freeParamMem(argvParamList *pList) {
    if (pList) {
        argvParamItem *lastItem;
        argvParamItem *it = pList->start;
        // Frees all items and its contents
        while (it) {
            if (it->extKey)
                free(it->extKey);
            if (it->value)
                free(it->value);
            if (it->helpMsg)
                free(it->helpMsg);
            lastItem = it;
            it = it->next;
            free(lastItem);
        }
        free(pList);
    }
    return;
}

short parseParams(argvParamList *pList, short argc, char *argv[]) {

    argvParamItem *it = pList->start;
    short i, aLen;
    for (i=1; i<argc; i++) {
        it = pList->start;
        while (it) {
            aLen = strlen(argv[i]);
            if ( (it->key[0] && !strncmp(argv[i], it->key, aLen) ) ||       // If key matches or
                 (it->extKey && !strncmp(argv[i], it->extKey, aLen) )       // if extKey matches
                ) {
                // if bool param type, no more argv required for it
                if (it->boolVal) {                                          // If is a boolean type param ...
                    it->value = malloc(2);                                  // Allocate chars for minimum value
                    strncpy(it->value, " ", 2);                             // Copies also \0
                    break;
                }
                else {
                    if ( !(i+1 == argc)) {                                  // If still has cmd line params...
                        if (!(*argv[i+1] == '-') ) {                        // Also if next cmd line param is not a key ...
                            aLen = strlen(argv[i+1]) + 1;
                            it->value = malloc(aLen);
                            strncpy(it->value, argv[i+1], aLen);            // Copies also \0
                            i++;                                            // Skips next cmd line arg, because it was used here
                            break;
                        }
                    }
                    // If there is no more parameters in argv, cannot obtain value, print error message
                    else {
                        printf("Value for required for param %s %s not informed\n", it->key, it->extKey);
                        return -1;
                    }
                }
            }
            it = it->next;
        }
    }
    bool ok = true;
    it = pList->start;
    while (it) {
    /*
     * Need to check all parameters. If some required params has value NULL
     * them it means no argv key was provided
     */
        // If required and do not have value, it is missing
        if (it->req && !it->value) {
            ok = false;
            printf("Required param %s %s not informed\n", it->key, it->extKey);
        }
        it = it->next;
    }
    if (ok)
        return 0;
    else
        return -1;
}

// Used for boolean parameter keys
bool getParamState(argvParamList *pList, char *key, char *extKey) {
    bool retVal = false;
    argvParamItem *it = pList->start;
    while (it) {
        if ( (it->value) &&
            ( (key && it->key[0] && !strcmp(key, it->key) ) ||       // If key matches or
              (extKey && it->extKey && !strcmp(extKey, it->extKey)) ) // if extKey matches
            ) {
            retVal = true;
            break;
        }
        it = it->next;
    }
    return retVal;
}

// Used for key->value pair based parameters
char* getParamValue(argvParamList *pList, char *key, char *extKey) {
    char *retVal = NULL;
    argvParamItem *it = pList->start;
    while (it) {
        if ( (key && it->key[0] && !strcmp(key, it->key) ) ||       // If key matches or
             (extKey && it->extKey && !strcmp(extKey, it->extKey) ) // if extKey matches
            ) {
            retVal = it->value;
            break;
        }
        it = it->next;
    }
    return retVal;
}
