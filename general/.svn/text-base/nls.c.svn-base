#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <syslog.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>

#include <sys/types.h>

#define MAX_BUF 1024
#define REAL_LS "/bin/ls0"
#define ALERT_THR 3
#define LOGFILE "/var/log/nls.log"

void build_command(FILE *fp,char *base,int argc,char *argv[])
{
   int n;

   fputs(base,fp);

   for (n=1; n<argc; n++)
      {
      putc(' ',fp);
      fputs(argv[n],fp);
      }

   putc('\n',fp);
}

void notify(time_t start_t,time_t elapsed_t,int argc,char *argv[])
{
   char cwd[MAX_BUF+1];
   double load[3];
   double l;
   FILE *fp;
   uid_t me;

   if (fp=fopen(LOGFILE,"a"))
      {
      l=(getloadavg(load,3)==-1)?-1:load[0];

      gethostname(cwd,MAX_BUF);
      fputs(cwd,fp);

      fprintf(fp,",%d,%d,%.2f,%d,%s,",start_t,elapsed_t,l,me=getuid(),
         getcwd(cwd,MAX_BUF));

      build_command(fp,REAL_LS,argc,argv);
      fclose(fp);

      sprintf(cwd,"NLS: event from user %d lasted %d seconds",
         me,elapsed_t);

      syslog(LOG_NOTICE,cwd);
      }
   else
      fprintf(stderr,"Error: failed to log event to %s\n",LOGFILE);
}

int main(int argc,char *argv[])
{
   time_t start_t,elapsed_t;
   pid_t pid;

   time(&start_t);
   if ((pid=fork())==0) /* child */
      {
      execv(REAL_LS,argv);
      exit(-1);
      }
   else /* parent */
      waitpid(pid,0,0);

   if ((elapsed_t=time(NULL)-start_t)>=ALERT_THR)
      notify(start_t,elapsed_t,argc,argv);

   return 0;
}
