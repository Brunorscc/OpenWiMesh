#!/bin/bash
#Script chama tudo
# é só passar as pastas iniciais e finais 
# p/ formar uma sequencia de numeros
# 

START=$1
FINISH=$2

for i in $(seq $START $FINISH);
do
	LOCAL="/home/openwimesh/capturas/$1"
	#if [ -d "$LOCAL" ]
	#then
	#	echo "A pasta '$LOCAL' não existe. Favor checar."
	#	exit
	#fi

done

for i in $(seq $START $FINISH);
do
	LOCAL="/home/openwimesh/capturas/$i"
	####### CALC DATAPLANE TRAFFIC ###########
	DUMP_FLOWS="$LOCAL/dump-flows"
	DPLANE_TRAFFIC="$LOCAL/dplane-traffic"
	#FLOWS-GERAL="DUMP-FLOWS/geral"
	FLOWS_OWN_TO_CTLR="$LOCAL/dplane-traffic/self_to_ofctl"
	FLOWSCTLR_TO_SELF="$LOCAL/dplane-traffic/ofctl_to_self"
	echo "OWN= $FLOWS_OWN_TO_CTLR"
	#mkdir $FLOWS-GERAL
	#`mkdir -vp $FLOWS_OWN_TO_CTLR`
	#`mkdir -vp $FLOWS_CTLR_TO_SELF`

	for cada in `ls $DUMP_FLOWS`
	do
		# GLOBAL CTLR
		# TODO: SOMAR TODOS OS VALORES DE PACOTES E BYTES DOS, POSSIVEIS, MULTIPLOS VIZINHOS DIRETAMENTE CONECTADOS
		# SOMAR TUDO QUE CASA COM O REGEX() E ESTÁ ENTRE OS TIMESTAMPS (de regex ^[0-9]) 
		#`cat $DUMP-FLOWS/$cada | grep ""`

		# CTLR TO SELF
		`cat $DUMP_FLOWS/$cada | grep "tcp,nw_src=192.168.199.254" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' >> $DPLANE_TRAFFIC/$cada`
		# SELF TO CTLR
		`cat $DUMP_FLOWS/$cada | grep "in_port=65534,nw_dst=192.168.199.254,tp_dst=6633" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $DPLANE_TRAFFIC/$cada`
	done

done

#python test-calc-dataplane-own-to-ctlr.py $FLOWS-GERAL
#python calc-dataplane-own-to-ctlr.py $FLOWS_OWN_TO_CTLR
#python calc-dataplane-own-to-ctlr.py $FLOWS_CTLR_TO_SELF