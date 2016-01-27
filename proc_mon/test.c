/* 
 *  proc_mon.c
 *
 *  2016.01.16  John Dey
 *
 *  Log user level commands with command line arguments. Log messages 
 *  are written in JSON format to /var/log/proc_mon.log. Listen to all
 *  kernel process events with proc connector.  proc_mon receives notification
 *  of all process events from the kernel.
 *
 *  Process events are delivered through a socket-based 
 *  interface by reading instances of struct proc_event defined in the 
 *  kernel header. Netlink is used to transfer information between kernel 
 *  modules and user space processes.  
 *
 *  Filter process events for EXEC and only log processes messages from
 *  non-root users.
 *
 *  Most of the code is liberally copied from Matt Helsley's proc 
 *  connector test code. 
 *
 *  improve by filtering at Kernel level before messages are sent
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/connector.h>
#include <linux/cn_proc.h>
#include <signal.h>
#include <errno.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/stat.h>
#include <syslog.h>
#include <linux/a.out.h>
#include <fcntl.h>



/*
 * pid  = process ID
 *
 * given a PID get the command line and UID
 * of a process
 *
 * Perform minimal cleanup of 'cmdline' for JSON output; 
 *   escape double quote " becomes \"
 *   escape escape char \ becomes \\
 *   and remove control charaters. 
 */
void
proc_cmdline(char *buf)
{
    int slen, i, j;
    char cmdline[4096], outbuf[4096];

    slen = strlen( buf ); 
    for(i=0,j=0; i<slen; i++) 
       if (buf[i] == '\0')
          cmdline[j++] = ' '; 
       else if (buf[i] < 32 || buf[i] > 127 ) /* remove control char */
          continue;
       else if ( buf[i] == '"' || buf[i] == '\\') {
          cmdline[j++] = '\\'; 
          cmdline[j++] = buf[i];
       }
       else
          cmdline[j++] = buf[i];
    cmdline[j] = '\0';
    if ((int)slen > 0) {
       snprintf(outbuf, sizeof(outbuf), "{\"cmdline\": \"%s\"}", cmdline);
       puts(outbuf);
    }
}

int 
main(int argc, const char *argv[])
{
    char buf[4096];

    while  ( fgets(buf, 4096, stdin) ) {
       proc_cmdline(buf);       
    }
}
