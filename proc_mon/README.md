Linux Process Monitoring
========================

### proc_mon ###

Monitor and log kernel exec events.  Recieve kernel process information 
from kernel proc connector.  All kernel proc events are recieved but
only exec events by non-root users are processed and logged.  Exec events 
are written to /var/log/proc_mon.log file in JSON format. The following 
information is writen to the log file:  timestamp, host, pid, uid, cmdline

### Install ###
Tested on Ubuntu LTS 14.04

```
cp proc_mon /usr/local/bin/proc_mon
cp proc_mon.init to /etc/init.d/proc_mon
sudo update-rc.d proc_mon defaults

#Start 
/etc/init.d/proc_mon start 
```

### Author ###
John Dey 2016

