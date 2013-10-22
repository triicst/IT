#!/bin/bash

logger -i -t leftover " started on `date`"

# This parameter governs how long between sending the default
# signale and SIGKILL to rogue processes
TIMEOUT=90

KILL=false
while [ $# -gt 0 ] ; do
    case $1 in
        -k) KILL=true ; shift 1 ;;
        *) shift 1 ;;
    esac
done

# Also kill if run in a non-interactive session (e.g. cron)
# If stdout is closed, then we are in a non-interactive session
if [ \! -t 0 ]
then
    KILL=true
fi

reserved="avahi daemon ganglia haldaemon halevt lp messagebus munge nobody ntp postfix root statd syslog www-data landscape sshd"

# users supposed to be running on node
queued=`squeue -a -h -w \`hostname\` -o "%u"|sort -u`
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
            logger -i -t leftover " killing all jobs owned by ${i}"
            killall -u ${i}
            sleep ${TIMEOUT}
            killall -9 -u ${i}
        else
            logger -i -t leftover " ${i} shouldn't be running"
        fi
    fi
done

# prune files/directories not accessed in last 7 days
find /tmp -atime +7 -print0 | xargs -0 /bin/rm -rf

