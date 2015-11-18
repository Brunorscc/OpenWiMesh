#!/bin/bash
# Autor: Bruno Ramos
# Comparativos de desempenho do trab final de Madson de multiplos controladores no openwimesh
# script calculo variancia e desvio padrão da latência e tempo de convergencia
# print no stdout

# padrão esperado: 
# MAC	/	TIMESTAMP	/	DELAY
#00:00:00:aa:00:00,15-11-07 18:32:23,5.495071

#PASTA="`pwd`/$1"
PASTA=$1

for cada in `ls $PASTA`
do
	MEDIA=`awk -F, '{s+=$3} END {print s/NR}' $PASTA$cada`
	#LINHAS=`wc -l $PASTA$cada`
	#MEDIA=$(( SOMA LINHAS))
	#awk -F, '{sum += $3; sum2 += $3*$3} END {print $1 " Media: " sum/NR "ms , VAR:" (sum2 - NR*((sum/NR)*(sum/NR))/(NR-1))}' $PASTA$cada
	#awk -F, '{sum += $3; sum2 += $3*$3} END {print $1 " Media: " sum/NR "ms , VAR:" ((sum*sum) - sum2)/(NR-1)}' $PASTA$cada
	#awk -F, '{sum += $3; sum2 += $3*$3} END {media= sum/NR; print $1 " Media: " media} 
	#START #{s+=(($3 - media)^2) VAR:" (sum2 - NR*((sum/NR)*(sum/NR))/(NR-1))}' $PASTA$cada
	#echo "$cada = $MEDIA ms"
	
	awk -F, '{s=$3;  v+=((s-$MEDIA)^2)} END {print "VAR:" v/NR}' $PASTA$cada
	#echo "$cada = $VAR "

#	awk -F, '{
 # min = max = sum = $3;       # Initialize to the first value (3rd field)
 # sum2 = $3 * $3              # Running sum of squares
 # for (n=NR; n <= NF; n++) {   # Process each value on the line
 #   if ($n < min) min = $n    # Current minimum
 #   if ($n > max) max = $n    # Current maximum
 #   sum += $n;                # Running sum of values
 #   sum2 += $n * $n           # Running sum of squares
 # }
 # print $1 ": min=" min ", avg=" sum/(NF-1) ", max=" max ", var=" ((sum*sum) - sum2)/(NF-1);
#}' $PASTA$cada
done

