#!/bin/bash
#create-dirs-capture.sh

MONIT=$1

LISTA_DIR=(dump-cpu-mem delay-slowpath latencia tempo-converg dump-flows dplane-traffic)

mkdir /home/openwimesh/capturas/$MONIT

for cada in ${LISTA_DIR[*]};
do
	rm -fr /home/openwimesh/capturas/$cada
	mkdir /home/openwimesh/capturas/$MONIT/$cada
	mkdir /home/openwimesh/capturas/$cada
	chown openwimesh:openwimesh /home/openwimesh/capturas/$cada
done