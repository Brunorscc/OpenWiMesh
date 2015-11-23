#!/bin/bash

EXEC=$1

DIR_EXEC=`ls /tmp | grep pycore`
NODES=`ls /tmp/$DIR_EXEC/ | grep conf`

CAPT="/home/openwimesh/capturas/$EXEC"

while [ -d "$CAPT" ]
do
	echo -e "ERRO: A pasta '$EXEC' já existe.\n  Escolha um novo nome para a pasta de dump monitoramento:"
	read EXEC
	CAPT="/home/openwimesh/capturas/$EXEC"
done

mkdir "$CAPT"


	echo "QUAL COMENTARIO GOSTARIA DE INSERIR SOBRE A TOPOLOGIA? "

	read choice

	echo "$choice" > "$CAPT/coments.txt"

for cada in $NODES
do
	
	cp -r /tmp/$DIR_EXEC/$cada /home/openwimesh/capturas/$EXEC
	
done

cp -r /home/openwimesh/capturas/delay-slowpath /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/dplane-traffic /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/dump-cpu-mem /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/latencia /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/tempo-converg /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/dump-flows /home/openwimesh/capturas/$EXEC
cp -r /home/openwimesh/capturas/latencia-global /home/openwimesh/capturas/$EXEC

ATUAL=`cat /home/openwimesh/capturas/monit-atual.conf | awk 'NR==1'`

cp -r /home/openwimesh/capturas/$ATUAL/* $CAPT/

ARQ1="/home/openwimesh/capturas/captura-$EXEC"
ARQ2="/home/openwimesh/capturas/captura-$EXEC.tar.gz"

if [ -e "$ARQ2" ]
then
while true
	do
		i=$((i+1))
		ARQtemp="$ARQ1.$i.tar.gz"
		if [ ! -e "$ARQtemp.tar.gz" ]
		then
			tar -zcvf $ARQtemp $CAPT
			break
		fi
 
	done
else

	tar -zcvf $ARQ2 $CAPT
fi