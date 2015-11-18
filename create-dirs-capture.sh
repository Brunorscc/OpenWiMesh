#!/bin/bash
#create-dirs-capture.sh

MONIT=$1

LISTA_DIR=(latencia tempo-converg dump-flows dplane-traffic delay-pktin delay-installrules)

mkdir /home/openwimesh/capturas/$MONIT

for cada in ${LISTA_DIR[*]};
do
	mkdir /home/openwimesh/capturas/$MONIT/$cada
done