#!/bin/bash

rm /root/.ssh/known_hosts
echo $1
PWD=$(pwd)
case "$1" in
	1) perl /home/openwimesh/novo-controlador.pl $PWD $1 $2 $3 $4 $5 $6 $7 $8 $9;;
	2) perl /home/openwimesh/novo-controlador.pl $PWD $1 $2 $3 $9;;
esac

