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

int  DEBUG =0;  /* FLAG set if cmd line arg is specifified */  
char Hostname[1024];
void get_cmdline(pid_t pid);

/*
 * connect to netlink
 * returns netlink socket, or -1 on error
 */
static int 
nl_connect()
{
    int rc;
    int nl_sock;
    struct sockaddr_nl sa_nl;

    nl_sock = socket(PF_NETLINK, SOCK_DGRAM, NETLINK_CONNECTOR);
    if (nl_sock == -1) {
        perror("socket");
        return -1;
    }

    sa_nl.nl_family = AF_NETLINK;
    sa_nl.nl_groups = CN_IDX_PROC;
    sa_nl.nl_pid = getpid();

    rc = bind(nl_sock, (struct sockaddr *)&sa_nl, sizeof(sa_nl));
    if (rc == -1) {
        perror("bind");
        close(nl_sock);
        return -1;
    }
    return nl_sock;
}

/*
 * turn on/off the proc events (process notifications)
 * enable bool:  Listen/Ignore
 *
 */
static int 
set_proc_ev_listen(int nl_sock, bool enable)
{
    int rc;
    struct __attribute__ ((aligned(NLMSG_ALIGNTO))) {
        struct nlmsghdr nl_hdr;
            struct __attribute__ ((__packed__)) {
                struct cn_msg cn_msg;
                enum proc_cn_mcast_op cn_mcast;
           };
    } nlcn_msg;

    memset(&nlcn_msg, 0, sizeof(nlcn_msg));
    nlcn_msg.nl_hdr.nlmsg_len = sizeof(nlcn_msg);
    nlcn_msg.nl_hdr.nlmsg_pid = getpid();
    nlcn_msg.nl_hdr.nlmsg_type = NLMSG_DONE;

    nlcn_msg.cn_msg.id.idx = CN_IDX_PROC;
    nlcn_msg.cn_msg.id.val = CN_VAL_PROC;
    nlcn_msg.cn_msg.len = sizeof(enum proc_cn_mcast_op);

    nlcn_msg.cn_mcast = enable ? PROC_CN_MCAST_LISTEN : PROC_CN_MCAST_IGNORE;

    rc = send(nl_sock, &nlcn_msg, sizeof(nlcn_msg), 0);
    if (rc == -1) {
       perror("netlink send");
       return -1;
    }

    return 0;
}

/*
 * handle a single process event
 */
static volatile bool need_exit = false;
static int 
handle_proc_ev(int nl_sock)
{
    int rc;
    struct __attribute__ ((aligned(NLMSG_ALIGNTO))) {
        struct nlmsghdr nl_hdr;
        struct __attribute__ ((__packed__)) {
            struct cn_msg cn_msg;
            struct proc_event proc_ev;
    };
    } nlcn_msg;

    while (!need_exit) {
        rc = recv(nl_sock, &nlcn_msg, sizeof(nlcn_msg), 0);
        if (rc == 0) {
            /* shutdown? */
            return 0;
        } else if (rc == -1) {
            if (errno == EINTR) 
                continue;
            perror("netlink recv");
            return -1;
        }
        if (nlcn_msg.proc_ev.what == PROC_EVENT_EXEC) {
            get_cmdline( nlcn_msg.proc_ev.event_data.exec.process_tgid);
        }
    }
    return 0;
}

/*
 *  
 */
FILE *logfp;          /* output log file */ 
const char* log_name = "/var/log/proc_mon.log";

void
open_log()
{
    if ( DEBUG == 1 )     /* debug mode is set */
       logfp == stderr;
    else 
       if ((logfp = fopen(log_name, "a")) == NULL) {
           syslog(LOG_ERR, "could not open %s: %m", log_name);
           exit(EXIT_FAILURE); 
       }
}

/*
 *  pointer to ISO 8601 timestamp
 *  not thread safe
 */
#include <time.h>
#include <sys/time.h>
char*
ISO8601_timestamp()
{
    static char ts[32];
    time_t uct_sec;
    struct tm *uct_tm; 
 
    uct_sec = time(NULL);
    uct_tm = gmtime(&uct_sec);
    snprintf(ts, sizeof(ts), "%d.%d.%dT%02d:%02d:%02dZ",
       uct_tm->tm_year+1900,
       uct_tm->tm_mon + 1,
       uct_tm->tm_mday,
       uct_tm->tm_hour,
       uct_tm->tm_min,
       uct_tm->tm_sec );
   return ts;
}

/*  write JSON formated message
 *  add timestamp and hostname
 */
#define BUFSZ 8192    /* twice size of PAGESIZE */
void
write_msg(char* msg)
{
    int count;
    char buf[BUFSZ];

    if ((count = snprintf(buf, BUFSZ, "{\"timestamp\": \"%s\", \"host\": \"%s\", %s}\n", ISO8601_timestamp(), Hostname, msg))
        != -1 ) 
        fputs(buf, logfp);
}

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
 *  
 * Note: /proc/pid/cmdline is 4096 in size.
 */
void
get_cmdline(pid_t pid)
{
    char fname[32], buf[4096], outbuf[BUFSZ+1], cmdline[BUFSZ+1];
    struct stat f;
    int i, j, count, slen, fd;

    snprintf(fname, sizeof(fname), "/proc/%ld", (long)pid);
    if ( lstat( fname, &f) == -1) 
       return;
    if ( f.st_uid == 0 )  /* Only collect Non-root events! */
       return;
    snprintf(fname, sizeof(fname), "/proc/%ld/cmdline", (long)pid);
    if ( (fd = open(fname, O_RDONLY)) == -1)
       return;
    slen = (int)read(fd, buf, (size_t)4096);
    close(fd);
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
       count = snprintf(outbuf, BUFSZ, "\"uid\": %ld, \"pid\": %ld, \"length\": %d, \"cmdline\": \"%s\"", 
            (long)f.st_uid, (long)pid, slen, cmdline);
       if (count != -1)
           write_msg(outbuf);
    }
}

/*
 * TERM and INT both cuase us to terminate 
 */
static void 
on_sigint(int unused)
{
    syslog(LOG_NOTICE, "terminated");
    write_msg("\"proc_mon\": \"terminated\"");
    void closelog();
    need_exit = true;
}

void
print_help(const char* name)
{
    printf("%s: Monitor kernel Proc Connector.\n", name);
    fputs(" write non-root Exec calls to /var/log/proc_mon.log\n", stdout);
    fputs(" --help print this message\n", stdout); 
    fputs(" --debug write messages to to standard out stay if forground\n", stdout); 
    fputs(" --daemon detach process and write messages to logfile\n", stdout); 
    fputs("  debug and daemon modes are exclusive\n", stdout);
    exit(EXIT_SUCCESS);
}
/*
 * daemonize -- only for non systemd Linux
 * Save to remove this code with systemd (and update main)
 */

static void 
daemon_init()
{
    pid_t pid;

    /* Fork off the parent process */
    if ((pid = fork()) < 0)
        exit(EXIT_FAILURE); /* error */
    else if (pid != 0)          
        exit(EXIT_SUCCESS); /* Success: terminate the parent */

    /* On success: The child process becomes session leader */
    if (setsid() < 0)
        exit(EXIT_FAILURE);

    /* Fork off for the second time*/
    if ((pid = fork()) < 0)
        exit(EXIT_FAILURE);    /* An error occurred */
    else if (pid != 0)
        exit(EXIT_SUCCESS);  /* Success: Let the parent terminate */

    /* Set new file permissions */
    umask(0);

    /* Change the working directory to the root directory */
    chdir("/");

    /* Close all open file descriptors */
    int x;
    for (x = 0; x<3; x++)
        close (x);

    /* Open the log file */
    openlog ("proc_mon", LOG_PID, LOG_DAEMON);
}

/*
 * debug and daemon flags are exclusive; can't be both
 */
void
process_args(int argc, const char *argv[])
{
    int i;

    for(i=1; i<argc; i++)
        if ( !strcmp(argv[i], "--help") )
           print_help(argv[0]);
        else 
        if ( !strcmp(argv[i], "--debug") )
           DEBUG == 1;
        else
        if  ( !strcmp(argv[i], "--daemon") ) {
           daemon_init();
           syslog(LOG_NOTICE, "starting");
        }
}

int 
main(int argc, const char *argv[])
{
    int nl_sock;
    int rc = EXIT_SUCCESS;

    process_args(argc, argv);

    /* Catch, ignore and handle signals */
    signal(SIGINT, &on_sigint);
    signal(SIGHUP, &on_sigint);
    siginterrupt(SIGINT, true);

    gethostname(Hostname, 1024);
    open_log();

    nl_sock = nl_connect();
    if (nl_sock == -1)
        exit(EXIT_FAILURE);

    write_msg("\"proc_mon\": \"started\"");
    rc = set_proc_ev_listen(nl_sock, true);
    if (rc == -1) {
        rc = EXIT_FAILURE;
        goto out;
    }

    rc = handle_proc_ev(nl_sock);
    if (rc == -1) {
        rc = EXIT_FAILURE;
        goto out;
    }

    set_proc_ev_listen(nl_sock, false);

out:
    close(nl_sock);
    exit(rc);
}
