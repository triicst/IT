#!/usr/bin/env python

# Accounting post-processor from Slurm job completion logs

import sys,getopt,hostlist
import datetime,time
import numpy
import gzip

# need 2.7 or better for datetime.timedelta.total_seconds()
if sys.hexversion<0x02070000:
   raise RuntimeError, "Python 2.7 or higher required"

def date_str(day):
   return "%4d-%02d-%02d" % (day[0],day[1],day[2])

def day_range(start,stop):
   days_in_month=[31,28,31,30,31,30,31,31,30,31,30,31]

   seq=[date_str(start)]

   if start==stop:
      return seq 

   r_start=start[:]

   while True:
      if r_start[2]<days_in_month[r_start[1]-1]:
         r_start[2]+=1
      else:
         r_start[2]=1
         if r_start[1]<12:
            r_start[1]+=1
         else:
            r_start[1]=1
            r_start[0]+=1

      seq.append(date_str(r_start))

      if r_start==stop:
         return seq

# parse Slurm time format yyyy-mm-ddThh:mm:ss ex:2011-01-04T11:33:03
def parse_time(job_comp_time):
   date_str,time_str=job_comp_time.split('T')
   date=map(int,date_str.split('-'))
   time=map(int,time_str.split(':'))

   d=datetime.date(date[0],date[1],date[2])
   t=datetime.time(time[0],time[1],time[2])

   return datetime.datetime.combine(d,t),date,time

def t_to_m(t):
   return t[0]*60+t[1]

def apportion_cores(cores_day,start_day,start_t,end_day,end_t,cores):
   day_span=day_range(start_day,end_day)
   for day in day_span:
      if day not in cores_day:
         cores_day[day]=numpy.zeros(24*60,int)

      if len(day_span)==1:
         cores_day[day][t_to_m(start_t):t_to_m(end_t)]+=cores
      else:
         if day==day_span[0]: # 1st in span
            cores_day[day][t_to_m(start_t):t_to_m([23,59,59])]+=cores
         elif day==day_span[-1]: # if last in span
            cores_day[day][t_to_m([0,0,0]):t_to_m(end_t)]+=cores
         else:
            cores_day[day]+=cores

# support compressed files too
def open_both(filename,mode):
   if filename[-3:]==".gz":
      return gzip.open(filename,mode)
   else:
      return open(filename,mode)

# should limit between start and end time interval
def read_job_completions(filename,start_report,end_report,skip_users,
   partitions,hr,cores_day,only_users=[],top_users=0):
   first=0 # first time stamp detected

   try:
      for line in open_both(filename,'r'):
         parse_state=0
         for field in line.strip().split():
            if '=' not in field: # probably failed job
               continue
            name,value=field.split('=',1)
            # Ignore FAILED and NODE_FAIL jobs
            if name=="JobState" and value not in ["COMPLETED","CANCELLED"]:
               parse_state=1
               break
            if name=="UserId": # assume uid(uidnumber) format
               user=value.split('(')[0]
               if user in skip_users or (only_users and user not in only_users):
                  parse_state=1
                  break
            elif name=="StartTime":
               if value=="Unknown": # weirdness observed >=2.2.3
                  parse_state=1
                  break
               start_time,start_day,start_t=parse_time(value)
               start_month=value[0:7]
               start_hour=int(value[11:13])
               if hr and (start_hour<hr[0] or start_hour>hr[1]):
                  parse_state=1
                  break
               if start_report and start_time<start_report:
                  parse_state=1
                  break
            elif name=="EndTime":
               end_time,end_day,end_t=parse_time(value)
               if end_report and end_time>end_report:
                  parse_state=1;
                  break
            elif name=="ProcCnt":
               cores=int(value)
               if cores==0:
                  parse_state=1
                  break
            elif name=="Partition":
               if partitions and value not in partitions:
                  parse_state=1
                  break

         if parse_state==0 and start_time<=end_time:
            elapsed_time=cores*(end_time-start_time)

            if first==0:
               low_time=start_time
               high_time=end_time
               first=1

            if low_time>start_time:
               low_time=start_time
            if high_time<end_time:
               high_time=end_time

            if only_users or top_users>0:
               if not user in cores_day:
                  cores_day[user]={}
               apportion_cores(cores_day[user],start_day,start_t,end_day,end_t,cores)
            else:
               apportion_cores(cores_day,start_day,start_t,end_day,end_t,cores)

   except IOError:
      print "Error: cannot open completions file '"+filename+"'"

def parse_epoch_time(epoch_sec):
   time_tuple=time.localtime(epoch_sec)

   t_date=map(lambda x:time_tuple[x],[0,1,2])
   t_time=map(lambda x:time_tuple[x],[3,4,5])

   return t_date,t_time

def read_moab_log(filename,start_report,end_report,skip_users,hour_range,
   cores_day):
   try:
      for num,line in enumerate(open_both(filename,'r')):
         if num>0:
            fields=line.strip().split(',')

            cores=int(fields[-1])

            start_time=int(fields[5])
            start_day,start_t=parse_epoch_time(start_time)
            end_day,end_t=parse_epoch_time(start_time+int(fields[6]))

            apportion_cores(cores_day,start_day,start_t,end_day,end_t,cores)

   except IOError:
      print "Error: cannot open Moab log '"+filename+"'"

# parse time as mm-dd-yyyy into datetime
def parse_user_time(utimespec):
   utime=map(int,utimespec.split('-'))
   if len(utime)!=3:
      print "Error: time format is mm-dd-yyyy!"
      return 0
  
   return datetime.datetime.combine(datetime.date(utime[2],utime[0],utime[1]),
      datetime.time(0))

def core_report(cores_day):
   print "Date,MinCores,MaxCores,MeanCores,STDCores"
   for key in sorted(cores_day.iterkeys()):
      print "%s,%d,%d,%d,%d" % (key,numpy.min(cores_day[key]),numpy.max(cores_day[key]),numpy.mean(cores_day[key]),numpy.std(cores_day[key]))

def determine_top_users(cores_day,top_users):
   top_user_data=[]
   only_users=[]

   # build list of users with sum of max core usage
   for user,userdata in cores_day.iteritems():
      total=0
      for usedate,usedata in userdata.iteritems():
         total+=numpy.max(usedata)
      top_user_data.append([user,total]) 

   # derive sorted list of top users 
   num_users=top_users
   for user,cores in sorted(top_user_data,key=lambda x:x[1],reverse=True):
      if num_users>0 and cores>0:
         only_users.append(user) 
         num_users-=1

   return only_users 

def core_users_report(cores_day,only_users):
   print "Date,User,MaxCores"

   for user in only_users:
      if user in cores_day:
         for key in sorted(cores_day[user].iterkeys()):
            print "%s,%s,%d" % (key,user,numpy.max(cores_day[user][key]))

def usage():
   print "zoidberg [options] job_completion_log[.gz] ..."
   print "\t-s start_date : start time as mm-dd-yyyy"
   print "\t-e end_date : start time as mm-dd-yyyy"
   print "\t-u user : ignore records from user"
   print "\t-U user : generate reports only for user(s)"
   print "\t-p partition : only include records in Slurm partition"
   print "\t-w time_window: only include 24 hour range start-finish"
   print "\t-M moab_log[.gz] : process Moab formatted log"
   print "\t-T : generate reports only for top users (overrides -U)"

def main(argv):
   cores_day={}

   start_report=0
   end_report=0

   skip_users=[]
   partitions=[]

   hour_range=[]

   only_users=[]
   top_users=0

   try:
      opts,args=getopt.getopt(argv,"s:e:u:p:w:M:U:Th")

      for opt,arg in opts:
         if opt in ("-h"):
            usage()
            sys.exit()
         elif opt in ("-s"): # start date
            start_report=parse_user_time(arg)
         elif opt in ("-e"): # end date
            end_report=parse_user_time(arg)
         elif opt in ("-u"): # Skip anyone in group
            skip_users.extend(arg.split(','))
         elif opt in ("-U"): # Generate report for users in list
            only_users.extend(arg.split(','))
         elif opt in ("-p"): # add to list of included partitions
            partitions.extend(arg.split(','))
         elif opt in ("-w"): # hour range
            hour_range=map(int,arg.split('-'))
            if len(hour_range)!=2 or hour_range[1]<hour_range[0]:
               print "Error: invalid range!"
               usage()
         elif opt in ("-M"): # Moab log
            read_moab_log(arg,start_report,end_report,skip_users,
               hour_range,cores_day)
         elif opt in ("-T"): # Top users (need to spec #)
            top_users=10

      if not args and not cores_day: # if no files on cmdline
         usage()
      else:
         for filename in args:
            read_job_completions(filename,start_report,end_report,
               skip_users,partitions,hour_range,cores_day,only_users,top_users)

         if len(cores_day)>0:
            if top_users>0:
               only_users=determine_top_users(cores_day,top_users)

            if only_users:
               core_users_report(cores_day,only_users)
            else:
               core_report(cores_day)

   except getopt.GetoptError:
      usage()

if __name__ == '__main__':
   main(sys.argv[1:])
