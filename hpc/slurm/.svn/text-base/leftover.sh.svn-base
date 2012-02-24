#!/bin/bash

KILL=true
while [ $# -gt 0 ] ; do
	case $1 in
		-k) KILL=true ; shift 1 ;;
		*) shift 1 ;;
	esac
done

reserved="daemon haldaemon messagebus ntp nobody root postfix man sshd avahi ldap slurm wwwrun at"

# users supposed to be running on node
queued=`squeue -a -h -n \`hostname\` -o "%u"|sort -u`
#echo "queued: $queued"

# users actually running on node
actual=`ps h -eo user|sort -u`
#echo "actual: $actual"

total="$reserved $queued"

for i in $actual
do
	MATCH=false
	for j in $total
	do
		if [ ${j} == ${i} ] ; then
			MATCH=true
			break
		fi
	done
	if ! ${MATCH} ; then
		if ${KILL} ; then
			echo "`date`: killing all jobs owned by ${i}"
			killall -9 -v -u ${i}
		else
			echo "${i} shouldn't be running"
		fi
	fi
done

# prune files/directories not accessed in last day
find /tmp -atime +7 -print0 | xargs -0 /bin/rm -rf
