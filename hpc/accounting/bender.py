#!/usr/bin/env python

# Accounting post-processor from Slurm job completion logs

import sys,getopt,hostlist
import datetime,time
import gzip

import numpy

# need 2.7 or better for datetime.timedelta.total_seconds()
if sys.hexversion<0x02070000:
   raise RuntimeError, "Python 2.7 or higher required"

# assumed format of groups file is uid,division,group,manager
# with formal CSV header
def load_groups(filename):
   groups={}

   try:
      for num,line in enumerate(open(filename,'r')):
         if num>0: # skip header
            if line[0]!='#': # if not comment
               fields=line.strip().split(',')
               if len(fields)!=4: # error if all fields not present
                  print "Warning: skipping incomplete record for",fields[0]
               else:
                  groups[fields[0]]=fields[1:]

   except IOError:
      print "Error: cannot open groups file '"+filename+"'"

   return groups

# support compressed files too
def open_both(filename,mode):
   if filename[-3:]==".gz":
      return gzip.open(filename,mode)
   else:
      return open(filename,mode)

# parse Slurm time format yyyy-mm-ddThh:mm:ss ex:2011-01-04T11:33:03
def parse_time(job_comp_time):
   date_str,time_str=job_comp_time.split('T')
   date=map(int,date_str.split('-'))
   time=map(int,time_str.split(':'))

   d=datetime.date(date[0],date[1],date[2])
   t=datetime.time(time[0],time[1],time[2])

   return datetime.datetime.combine(d,t)

def dict_sum(dict,key,sum):
   try:
      dict[key]+=sum
   except KeyError:
      dict[key]=sum

def dict_sum_array(dict,key,alist):
   try:
      dict[key]+=numpy.array(alist)
   except KeyError:
      dict[key]=numpy.array(alist)

# should limit between start and end time interval
def read_job_completions(filename,groups,user_total,group_total,div_total,
   start_report,end_report,skip_users,partitions,no_bounds,monthly_members,
   mm,hr,user_jobs):
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
               if user in skip_users:
                  parse_state=1
                  break
            elif name=="StartTime":
               if value=="Unknown": # weirdness observed >=2.2.3
                  parse_state=1
                  break
               start_time=parse_time(value)
               start_month=value[0:7]
               start_hour=int(value[11:13])
               if hr and (start_hour<hr[0] or start_hour>hr[1]):
                  parse_state=1
                  break
               if start_report and start_time<start_report:
                  parse_state=1
                  break
            elif name=="EndTime":
               end_time=parse_time(value)
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

            dict_sum(user_total,user,elapsed_time)
            dict_sum_array(user_jobs,user,[cores,end_time-start_time,1])
            if groups:
               if user in groups:
                  dict_sum(group_total,groups[user][1],elapsed_time)
                  dict_sum(div_total,groups[user][0],elapsed_time)
               else:
                  print >> sys.stderr,"Warning: user",user,"has no groups entry!"
                  dict_sum(group_total,"Undefined",elapsed_time)
                  dict_sum(div_total,"Undefined",elapsed_time)
            if monthly_members:
               if user in monthly_members:
                  dict_sum(mm[0],start_month,elapsed_time)
               else:
                  dict_sum(mm[1],start_month,elapsed_time)

      if no_bounds==0:
         print "Bounds",low_time,"to",high_time

   except IOError:
      print "Error: cannot open completions file '"+filename+"'"

def parse_epoch_time(epoch_sec):
   time_tuple=time.localtime(epoch_sec)

   t_date=map(lambda x:time_tuple[x],[0,1,2])
   t_time=map(lambda x:time_tuple[x],[3,4,5])

   d=datetime.date(t_date[0],t_date[1],t_date[2])
   t=datetime.time(t_time[0],t_time[1],t_time[2])

   return datetime.datetime.combine(d,t)

def read_moab_log(filename,groups,user_total,group_total,div_total,
   start_report,end_report,skip_users,no_bounds,user_jobs):
   first=0 # first time stamp detected

   try:
      for num,line in enumerate(open_both(filename,'r')):
         if num>0:
            fields=line.strip().split(',')

            user=fields[2]
            if user in skip_users:
               continue

            start_time=int(fields[5])
            start_date=parse_epoch_time(start_time)
            if start_report and start_date<start_report:
               continue
               
            end_date=parse_epoch_time(start_time+int(fields[6]))
            if end_report and end_date>end_report:
               continue

            cores=int(fields[-1])
            if cores==0:
               continue

            if start_date<end_date:
               elapsed_time=cores*(end_date-start_date)

               if first==0:
                  low_time=start_date
                  high_time=end_date
                  first=1

               if low_time>start_date:
                  low_time=start_date
               if high_time<end_date:
                  high_time=end_date

               dict_sum(user_total,user,elapsed_time)
               dict_sum_array(user_jobs,user,[cores,end_date-start_date,1])
               if groups:
                  if user in groups:
                     dict_sum(group_total,groups[user][1],elapsed_time)
                     dict_sum(div_total,groups[user][0],elapsed_time)
                  else:
                     print >> sys.stderr,"Warning: user",user,"has no groups entry!"
                     dict_sum(group_total,"Undefined",elapsed_time)
                     dict_sum(div_total,"Undefined",elapsed_time)

      if no_bounds==0:
         print "Bounds",low_time,"to",high_time

   except IOError:
      print "Error: cannot open Moab log '"+filename+"'"

# report by users
def report_users(groups,users,csv,jobs):
   if users:
      if csv==0:
         print "Report by Users:"
      else:
         print "User,Group,Division,Time"

      total=datetime.timedelta(0) # accumulate all elapsed times

      # sort inverse by time consumed
      for item in sorted(users.iteritems(),key=lambda(k):k[1],reverse=True):
         if csv:
            if groups:
               if item[0] in groups:
                  group=groups[item[0]]
               else:
                  group=["Undefined","Undefined"]

               print '%s,%s,%s,%f' % (item[0],group[1],group[0],
                  item[1].total_seconds())
            else:
               print '%s,%f' % (item[0],item[1].total_seconds())
         else:
            print item[0],item[1],
            current_avg=jobs[item[0]]
            print "(Average time",current_avg[1]/current_avg[2],"cores",current_avg[0]/current_avg[2],"over",current_avg[2],"jobs)"
            total+=item[1]

      if csv==0:
         print "Total",total
         print

# report by groups
def report_group(group,title):
   if group:
      print title

      total=datetime.timedelta(0) # accumulate all elapsed times

      # sort inverse by time consumed
      for item in sorted(group.iteritems(),key=lambda(k):k[1],reverse=True):
         print item[0],item[1]
         total+=item[1]

      print "Total",total
      print

def report_monthly_members(mm,csv):
   if csv and mm:
      print "Month,Members,Others"

   for month in sorted(mm[0].keys()):
      if csv:
         print '%s,%f,%f' % (month,mm[0][month].total_seconds(),
            mm[1][month].total_seconds())
      else:
         print month,mm[0][month],mm[1][month]

# parse time as mm-dd-yyyy into datetime
def parse_user_time(utimespec):
   utime=map(int,utimespec.split('-'))
   if len(utime)!=3:
      print "Error: time format is mm-dd-yyyy!"
      return 0
  
   return datetime.datetime.combine(datetime.date(utime[2],utime[0],utime[1]),
      datetime.time(0))

def usage():
   print "bender [options] job_completion_log[.gz] ..."
   print "\t-g group_file : list of users by division, group, manager"
   print "\t-s start_date : start time as mm-dd-yyyy"
   print "\t-e end_date : start time as mm-dd-yyyy"
   print "\t-u user : ignore records from user"
   print "\t-p partition : only include records in partition"
   print "\t-c : output in csv format"
   print "\t-m member_list: divide by months, member_list and without"
   print "\t-w time_window: only include 24 hour range start-finish"
   print "\t-M moab_log[.gz] : process Moab formatted log"

def main(argv):
   groups={}   # dictionary of users by division,group,manager

   user_total={}  # time (cores * elapsed) per user
   group_total={} # time per group
   div_total={}   # time per division

   user_jobs={} # number of jobs submitted by user

   csv=0

   start_report=0
   end_report=0

   skip_users=[]
   partitions=[]

   monthly_members=[]
   mm=[{},{}]

   hour_range=[]

   try:
      opts,args=getopt.getopt(argv,"g:s:e:cu:p:m:w:M:h")

      for opt,arg in opts:
         if opt in ("-h"):
            usage()
            sys.exit()
         elif opt in ("-g"): # file containing groups
            groups=load_groups(arg)
         elif opt in ("-s"): # start date
            start_report=parse_user_time(arg)
         elif opt in ("-e"): # end date
            end_report=parse_user_time(arg)
         elif opt in ("-c"): # write output as csv
            csv=1 
         elif opt in ("-u"): # Skip anyone in group
            skip_users.extend(arg.split(','))
         elif opt in ("-p"): # add to list of included partitions
            partitions.extend(arg.split(','))
         elif opt in ("-m"): # monthly member_list and without
            monthly_members=arg.split(',')
         elif opt in ("-w"): # hour range
            hour_range=map(int,arg.split('-'))
            if len(hour_range)!=2 or hour_range[1]<hour_range[0]:
               print "Error: invalid range!"
               usage()
         elif opt in ("-M"): # Moab log
            read_moab_log(arg,groups,user_total,group_total,div_total,
               start_report,end_report,skip_users,csv,user_jobs)

      if not args and not user_total: 
         usage()
      else:
         for filename in args:
            read_job_completions(filename,groups,user_total,group_total,
               div_total,start_report,end_report,skip_users,partitions,csv,
               monthly_members,mm,hour_range,user_jobs)

         if monthly_members:
            report_monthly_members(mm,csv)
         else: 
            report_users(groups,user_total,csv,user_jobs)
            if csv==0: # only output user list if csv output specified
               report_group(group_total,"Groups:")
               report_group(div_total,"Divisions:")

   except getopt.GetoptError:
      usage()

if __name__ == '__main__':
   main(sys.argv[1:])
