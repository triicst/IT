/* C reimplementation of downboy sans system() */

#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <unistd.h>
#include <alloca.h>
#include <stdlib.h>
#include <signal.h>
#include <pwd.h>

#include <sys/time.h>
#include <sys/stat.h>
#include <sys/resource.h>

#define USER_HZ 100 /* probably wrong */

#define PROC_ROOT "/proc"

#define MAX_LEN 255

#define COUNT_DIGITS(name) strspn(name,"0123456789")

#define OVERRIDE_FILE "/usr/local/etc/downboy2.conf"

typedef struct override_struct {
   int uid;
   int elapsed;
   int priority;
   struct override_struct *next;
} override_type;

override_type *find_override(override_type *override_list,int uid)
{
   for (; override_list && uid!=override_list->uid;
      override_list=override_list->next)
      ;

   return(override_list);
}

override_type *load_override(char *filename)
{
   override_type *override_list=NULL;

   override_type *new_override;
   struct passwd *pw_entry;
   char uname[MAX_LEN];
   int utime,upri;
   FILE *fp;

   if (fp=fopen(filename,"r"))
      {
      while (!feof(fp))
         if (fscanf(fp,"%s %d %d\n",uname,&utime,&upri)==3 && *uname!='#')
            {
            if ((pw_entry=getpwnam(uname))==NULL)
               fprintf(stderr,"downboy2: user '%s' not in passwd list\n",uname);
            else
               {
               new_override=(override_type *)malloc(sizeof(override_type));

               new_override->uid=pw_entry->pw_uid;
               if (utime>0)
                  new_override->elapsed=utime*60; /* minutes to seconds */
               new_override->priority=upri;
               new_override->next=override_list;
               override_list=new_override;
               }
            }

      fclose(fp);
      }

   return(override_list);
}

char *make_name(char *proc_id,int stats)
{
   static char stat_filename[MAX_LEN+1];

   strcpy(stat_filename,PROC_ROOT);
   strcat(stat_filename,"/");
   strcat(stat_filename,proc_id);

   if (stats==1)
      strcat(stat_filename,"/stat");

   return(stat_filename);
}

/* return NULL after EOF */
char *get_next_field(FILE *fp)
{
   static char field[MAX_LEN+1];
   int n;
   int c;

   for (n=0; n<MAX_LEN && (c=getc(fp))!=' ' && c!=EOF; n++)
      field[n]=c;
   field[n]='\0';

   return((n==0)?NULL:field);
}

char *strip_parens(char *s)
{
   if (*s=='(')
      *(strrchr(s++,')'))='\0';

   return(s);
}

int get_new_priority(unsigned utime,int pid,override_type *entry)
{
   int priority=-1; /* do nothing */

   if (entry)
      {
      if (entry->elapsed==-1) /* if user is excluded then do nothing */
         return(-1);
      else
         {
         if (utime>entry->elapsed && 
            getpriority(PRIO_PROCESS,pid)<entry->priority)
            return(entry->priority); /* return override priority */
         }
      } 

   if (utime>3600) /* over 1 hour */
      {
      priority=15;
      if (utime>86400) /* over 1 day */
         priority=18;

      if (getpriority(PRIO_PROCESS,pid)>=priority)
         priority=-1; /* never increase priority or set to same */
      }

   return(priority);
}

void adjust_sched(int pid,char *proc_name,unsigned utime,int priority,int nice,
   override_type *entry)
{
   int new_pri;

   if ((new_pri=get_new_priority(utime,pid,entry))!=-1 && new_pri!=nice)
      {
      printf("%s(%d) was %d, now %d\n",proc_name,pid,nice,new_pri);

      if (setpriority(PRIO_PROCESS,pid,new_pri)!=0)
         fprintf(stderr,"Error: failed to set %s(%d) to priority %d!\n",
            proc_name,pid,new_pri);
      }
}

#define MSG_TEMPLATE "echo \"This system is _only_ for interactive use: limit is %d CPU seconds\"|mail %s@test.org -b petersen@fhcrc.org -s \"process %d killed on %s due to overtime\""

void kill_proc(int pid,int uid,int k)
{
   struct passwd *entry=getpwuid(uid); /* lookup username from uid */

   char hostname[80];
   char msg[1024];

   /* create and send kill notification */ 
   gethostname(hostname,79);
   sprintf(msg,MSG_TEMPLATE,k,entry->pw_name,pid,hostname);
   system(msg);

   printf("Trying to kill pid %d belonging to %s\n",pid,entry->pw_name);
   kill(pid,SIGKILL);
}

void read_stat(char *proc_id,override_type *entry,int k,int uid)
{
   char *stat_filename=make_name(proc_id,1);
   int done=0;

   char *field;
   FILE *fp;
   int n; /* current field number */

   char *proc_name;
   unsigned utime;
   int priority;
   int nice;

   if ((fp=fopen(stat_filename,"r"))==NULL)
      fprintf(stderr,"Error: failed to open '%s'!\n",stat_filename);
   else
      {
      for (n=0; !done && (field=get_next_field(fp)); n++)
         switch (n)
            {
            case 1: /* proc name */
               proc_name=alloca(strlen(field)+1);
               strcpy(proc_name,strip_parens(field));
               break;

            case 13: /* utime */
               utime=atol(field)/(float)USER_HZ;
               break;

            case 17: /* priority */
               priority=atoi(field);
               break;

            case 18: /* nice */
               nice=atoi(field);
               done=1; /* end iteration after last interesting field */
               break;
            }

      fclose(fp);
      }

   if (done) /* reached last field OK */
      {
      /* if exceeded defined kill threshold and not an exception... */
      if (k>0 && (!entry || entry->elapsed!=-1) && utime>k)
         kill_proc(atoi(proc_id),uid,k);
      else
         adjust_sched(atoi(proc_id),proc_name,utime,priority,nice,entry);
      }
}

int get_owner(char *proc_id)
{
   char *filename=make_name(proc_id,0);
   int uid=-1; /* error returned if stat not completed */

   struct stat file_stat;

   if (stat(filename,&file_stat)!=0)
      fprintf(stderr,"Error: failed to stat '%s'!\n",filename);
   else
      uid=file_stat.st_uid;

   return(uid);
}

main(int argc,char *argv[])
{
   int k=-1; /* kill threshold in CPU seconds */

   override_type *override_list;
   struct dirent *dir_entry_p;
   DIR *dir_p;
   int uid;

   int opt;

   while ((opt=getopt(argc,argv,"k:h"))!=-1)
      switch (opt)
         {
         case 'k': /* kill threshold in CPU seconds */
            if ((k=atoi(optarg))>0)
               break;

         case '?': /* miscellaneous error condition */
         case 'h': /* help! */
            fprintf(stderr,"downboy2 [-k kill_threshold_in_CPU_seconds]\n");
            exit(-1);
         }

   if ((dir_p=opendir(PROC_ROOT))==NULL)
      fprintf(stderr,"Error: failed to open '%s'!\n",PROC_ROOT);
   else
      {
      override_list=load_override(OVERRIDE_FILE);

      while ((dir_entry_p=readdir(dir_p))!=NULL)
         if (COUNT_DIGITS(dir_entry_p->d_name)==strlen(dir_entry_p->d_name)
            && (uid=get_owner(dir_entry_p->d_name))!=0) /* if not root */
            read_stat(dir_entry_p->d_name,find_override(override_list,uid),
               k,uid);

      closedir(dir_p);
      }
}
