#!/bin/bash
# Accounting collector script
# Jeff Katcher 3/25/09

ACCT_DIR=/var/account
ACCT_BASE="pacct-"

if [ -z $1 ]
then
	echo "Usage: `basename $0` month year"
	exit -1
else
	if (("$1" < "10"))
	then
		MONTH="0$1"
	else
		MONTH=$1
	fi
fi

if [ -z $2 ]
then
	YEAR=`date +%Y`
else
	YEAR=$2
fi

TEMPLATE="$ACCT_BASE$YEAR$MONTH*"
OUTPUT=$ACCT_DIR/`hostname`.$1

cd $ACCT_DIR
for acct_file in $TEMPLATE
do
	if [ "$acct_file" = "$TEMPLATE" ]
	then
		echo "Error: No accounting files match $acct_file!"
		exit -1
	else
		rm -f $OUTPUT
		echo "Extracting $acct_file to $OUTPUT"
		strip_gz=${acct_file%.gz}
		if [ "$strip_gz" = "$acct_file" ]
		then
			strip_bz2=${acct_file%.bz2}
			if [ "$strip_bz2" = "$acct_file" ]
			then
				echo "Error: suffix unknown!"
			else
				bunzip2 $acct_file
				sa -m $strip_bz2 >$OUTPUT.$strip_bz2
				bzip2 $strip_bz2
			fi
		else
			gunzip $acct_file
			sa -m $strip_gz >$OUTPUT.$strip_gz
			gzip $strip_gz
		fi
	fi
done

# collect output files into single file and delete individual ones
cat $OUTPUT.$TEMPLATE >$OUTPUT
rm $OUTPUT.$TEMPLATE

exit 0
