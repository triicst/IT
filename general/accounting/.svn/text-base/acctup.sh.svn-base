#!/bin/bash
# Accounting download script
# Jeff Katcher 3/25/09

ACCT_DIR=/var/account

if [ -z $1 ]
then
	echo "Usage: `basename $0` nodefile [month [year]]"
	exit -1
else
	NODEFILE=$1
	if [ ! -f $NODEFILE ]; then
		echo "Error: $NODEFILE does not exist!"
		exit -1
	elif [ ! -r $NODEFILE ]; then
		echo "Error: $NODEFILE cannot be read!"
		exit -1
	fi
fi

if [ -z $2 ]
then
	MONTH=`date +%-m`
else
	MONTH=$2
fi

if [ -z $3 ]
then
	YEAR=`date +%Y`
else
	YEAR=$3
fi

count=0
while read node
do
	nodes[$count]="$node"
	count=$(($count+1))
done <$NODEFILE

for node in ${nodes[@]}
do
	echo "Getting accounting info for $node"
	ssh root@$node collacct.sh $MONTH $YEAR
	scp root@$node:$ACCT_DIR/$node.$MONTH .
done

exit 0
