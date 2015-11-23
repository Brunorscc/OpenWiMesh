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

	FLOWS_OWN_TO_CTLR="$LOCAL/dplane-traffic/self_to_ofctl"
	FLOWS_CTLR_TO_SELF="$LOCAL/dplane-traffic/ofctl_to_self"
	#echo "OWN= $FLOWS_OWN_TO_CTLR"
	
	mkdir $FLOWS_OWN_TO_CTLR
	mkdir $FLOWS_CTLR_TO_SELF

	for cada in `ls $DUMP_FLOWS`
	do
		# CTLR TO SELF
		`cat $DUMP_FLOWS/$cada | grep "tcp,nw_src=192.168.199.254" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' >> $FLOWS_CTLR_TO_SELF/$cada`
		# SELF TO CTLR
		`cat $DUMP_FLOWS/$cada | grep "in_port=65534,nw_dst=192.168.199.254,tp_dst=6633" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $FLOWS_OWN_TO_CTLR/$cada`
	done

	DIR_LATENCY="$LOCAL/latencia"
	mkdir $LOCAL/latencia-filter

	for cada in `ls $DIR_LATENCY`
	do 
		`cat $DIR_LATENCY/$cada | awk -F',' '{print $3}' > $LOCAL/latencia-filter/$cada`
	done
done

#
echo -e "\nDATA PLANE - SELF TO CTLR\n"
python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/self_to_ofctl

echo -e "\nDATA PLANE - CTLR TO SELF"
python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/ofctl_to_self

#latencia
echo -e "\nLATENCIA"
python teste-calc-latency.py /home/openwimesh/capturas $START $FINISH latencia-filter
#python teste-calc-latency.py /home/openwimesh/capturas 100 100 latencia-filter