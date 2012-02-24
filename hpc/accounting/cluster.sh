#!/bin/bash

R_BATCH='R CMD BATCH --vanilla --slave --no-timing'

SUPPRESS='-u biguser'
ALL_SUPPRESS='-u root,nobody'

GROUPS=user-division-department-HPC.txt

LIMIT='-s 11-24-2011 -e 01-24-2012'
#LIMIT='-s 09-01-2011'
#LIMIT='-s 09-23-2011'

if [ -z $1 ]
then
	LOGFILE="slurmjobcomp.log"
else
	LOGFILE=$1
fi

if [ -z $2 ]
then
	PART=""
else
	PART="-p $2"
fi

echo "Processing job completions from $LOGFILE"

./bender.py $PART $LIMIT -g $GROUPS -c $ALL_SUPPRESS $LOGFILE >cluster_all.csv

echo "Generating figures for all users"
$R_BATCH '--args cluster_all.csv' cluster.r cluster_all.Rout
mv Rplots.pdf cluster_all.pdf

./bender.py $PART $LIMIT -g $GROUPS -c $ALL_SUPPRESS $SUPPRESS $LOGFILE >cluster_small.csv

echo "Generating figures for smaller users only"
$R_BATCH '--args cluster_small.csv' cluster.r cluster_small.Rout
mv Rplots.pdf cluster_small.pdf

echo "Generating core usage figures"
./zoidberg.py $PART $LIMIT $ALL_SUPPRESS $SUPPRESS $LOGFILE >zoid-nobiguser.csv
./zoidberg.py $PART $LIMIT $ALL_SUPPRESS $LOGFILE >zoid-all.csv
$R_BATCH cores.r cores.Rout
mv Rplots.pdf cores.pdf

echo "Generating top 10 core usage figures"
./zoidberg.py -T $PART $LIMIT $ALL_SUPPRESS $LOGFILE >cores-top10.csv
$R_BATCH '--args cores-top10.csv' cores_bar.r cores_bar.Rout
mv Rplots.pdf cores-top10.pdf
