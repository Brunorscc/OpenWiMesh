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
	FLOWS_CTLR_TO_GLOBAL="$LOCAL/dplane-traffic/ctlr_to_global"
	FLOWS_GLOBAL_TO_CTRL="$LOCAL/dplane-traffic/global_to_ctlr"
	#echo "OWN= $FLOWS_OWN_TO_CTLR"
	
	#if [ ! -d "$FLOWS_OWN_TO_CTLR" -a ! -d "$FLOWS_CTLR_TO_SELF" ! -d "$FLOWS_CTLR_TO_GLOBAL" -a ! -d "$FLOWS_GLOBAL_TO_CTRL"]
	#then 
		mkdir $FLOWS_OWN_TO_CTLR
		mkdir $FLOWS_CTLR_TO_SELF
		mkdir $FLOWS_CTLR_TO_GLOBAL
		mkdir $FLOWS_GLOBAL_TO_CTRL

		for cada in `ls $DUMP_FLOWS`
		do
			# CTLR TO SELF
			`cat $DUMP_FLOWS/$cada | grep "tcp,nw_src=192.168.199.254" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $FLOWS_CTLR_TO_SELF/$cada`
			# SELF TO CTLR
			`cat $DUMP_FLOWS/$cada | grep "in_port=65534,nw_dst=192.168.199.254,tp_dst=6633" | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $FLOWS_OWN_TO_CTLR/$cada`
		done
		echo "DUMP: $LOCAL/dump-cpu-mem"

		for cada in `ls $LOCAL/dump-cpu-mem/ | grep "\-ctrl"`
		do
			x="`echo $cada | sed 's/ctrl/flows/g'`"
			echo "##########AQUII $x"
			# CTLR TO GLOBAL
			`cat $DUMP_FLOWS/$x | grep '47922\|LOCAL' | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $FLOWS_GLOBAL_TO_CTRL/$x`
			
			# GLOBAL TO CTRL
			`cat $DUMP_FLOWS/$x | grep '47922\|output' | awk -F',' '{print $4"="$5}' | awk -F'=' '{print $2','$4}' > $FLOWS_CTLR_TO_GLOBAL/$x`
		done
	#fi

	DIR_LATENCY="$LOCAL/latencia"
	if [ ! -d "DIR_LATENCY" ]
	then
		mkdir $LOCAL/latencia-filter

		for cada in `ls $DIR_LATENCY`
		do 
			`cat $DIR_LATENCY/$cada | awk -F',' '{print $3}' > $LOCAL/latencia-filter/$cada`
		done
	fi
	#### NEW SLOWPATH 05/12 #####
	DIR_SLOW_PATH="$LOCAL/delay-slowpath"
	if [ ! -d "DIR_SLOW_PATH" ]
	then
		mkdir $LOCAL/delay-slowpath-filter
		mkdir $LOCAL/media-paths-filter

		for cada in `ls $DIR_SLOW_PATH`
		do
			#slow-path
			`cat $DIR_SLOW_PATH/$cada | grep seq=1 | grep seq= | cut -d' ' -f4,7 | sed 's/\: time=/,/g' >  $DIR_SLOW_PATH-filter/$cada`

			#media-delay
			`cat $LOCAL/media-paths/$cada | grep -v 'seq=1' | grep seq= | cut -d' ' -f4,7 | sed 's/\: time=/,/g' > $LOCAL/media-paths-filter/$cada`
		done
	fi
	#########
done

#
echo -e "\nDATA PLANE - SELF TO CTLR\n"
#python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/self_to_ofctl

echo -e "\nDATA PLANE - CTLR TO SELF"
#python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/ofctl_to_self

echo -e "\nDATA PLANE - CTRL TO GLOBAL\n"
python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/ctlr_to_global

echo -e "\nDATA PLANE - GLOBAL TO CTLR\n"
python calc-dataplane-own-to-ctlr.py /home/openwimesh/capturas $START $FINISH dplane-traffic/global_to_ctlr

#latencia
echo -e "\nLATENCIA"
python teste-calc-latency.py /home/openwimesh/capturas $START $FINISH latencia-filter
#python teste-calc-latency.py /home/openwimesh/capturas 100 100 latencia-filter