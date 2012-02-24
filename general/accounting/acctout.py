#!/usr/bin/env python

import sys,getopt

def field_to_num(field,sep):
   return(float(field.split(sep)[0]))

def sa_parse(filename,users):
   total_cp=0

   try:
      for line in open(filename,'r'):
         fields=line.split()
         if len(fields)==5: # total line lacks name field
            total_cp+=field_to_num(fields[2],"cp")
         else:
            if fields[0] in users: # if entry exists, sum
               users[fields[0]]+=field_to_num(fields[3],"cp")
            else: # create new entry
               users[fields[0]]=field_to_num(fields[3],"cp")
   except IOError:
      print "Error: cannot open sa file '"+filename+"'"

   return total_cp

def print_usage(name,value,total,censor,csv,groups):
   usage=value/total*100
   if usage>=censor:
      if csv==0:
         print '%s %.3f%%' % (name.ljust(12),usage)
      else:
         if groups:
            if name in groups:
               user_group=groups[name]
            else:
               user_group=["Undefined","Undefined"]
            print '%s,%f,%.3f,%s,%s' % (name,value,usage,user_group[0],user_group[1])
         else:
            print '%s,%f,%.3f' % (name,value,usage)

def sa_report_users(total_cp,users,csv,censor,groups):
   if csv==0:
      print "Report by Users:"
   else:
      if groups:
         print "User,CPU_Minutes,PercentOfTotal,Division,Group"
      else:
         print "User,CPU_Minutes,PercentOfTotal"

   for user in sorted(users.items(),key=lambda x: x[1],reverse=True):
      print_usage(user[0],user[1],total_cp,censor,csv,groups)

def sa_report_groups(total_cp,users,groups):
   print "Report by Groups:"

   totality=total_cp
   for group in sorted(groups.items()):
      group_total=0
      for user in group[1]:
         if user in users:
            group_total+=users[user]
      print_usage(group[0],group_total,total_cp,0)
      totality-=group_total

   if totality>0: # if remainder exists
      print
      print_usage("Remainder",totality,total_cp,0)

# assumed format of groups file is uid,division,group,manager
def load_groups(filename):
   groups={}

   try:
      for line in open(filename,'r'):
         if line[0]!='#': # if not comment
            fields=line.strip().split(',')
            if len(fields)!=4: # error if all fields not present
               print "Warning: skipping incomplete record for",fields[0]
            else:
               groups[fields[0]]=fields[1:]

   except IOError:
      print "Error: cannot open groups file '"+filename+"'"

   return groups

def load_filelist(filename,total_cp):
   try:
      for line in open(filename,'r'):
         #print "Importing",line.strip()
         total_cp=sa_parse(line.strip(),total_cp)
   except IOError:
      print "Error: cannot open files file '"+filename+"'"
   
   return total_cp

def delete_unpeople(unpeople,total_cp,users):
   for unperson in unpeople:
      total_cp-=users[unperson] # delete unperson contribution
      del users[unperson] # delete unperson

   return total_cp

def usage():
   print "acctout [-l sa_file_list][-g group_file][-u account][-C censor][-c] [sa_summary ...]"

def main(argv):
   total_cp=0  # total of cpu used
   users={}    # dictionary of users
   groups={}   # dictionary of groups
   unpeople=[] # list of people to ignore

   csv=0       # output standard report
   censor=0.001 # default sensor value

   try:
      opts,args=getopt.getopt(argv,"l:g:u:C:ch")
   except getopt.GetoptError:
      usage()
      sys.exit(2)

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-g"): # file containing groups
         groups=load_groups(arg)
      elif opt in ("-l"): # file containing list of file
         total_cp=load_filelist(arg,total_cp)
      elif opt in ("-u"): # unpeople
         unpeople.append(arg)
      elif opt in ("-c"): # csv output
         csv=1
      elif opt in ("-C"): # censor output below...
         censor=float(arg)
  
   if len(args)==0 and total_cp==0: # if no files on cmdline or filelist
      usage()
   else:
      for summary in args:
         total_cp+=sa_parse(summary,users)
         if total_cp==0:
            sys.exit(-1)
  
      total_cp=delete_unpeople(unpeople,total_cp,users) 

      # output user report   
      sa_report_users(total_cp,users,csv,censor,groups)

      # group report is broken because groups file is now groups-by-user
      # output group report if not csv output and groups exist 
      #if csv==0 and len(groups)>0:
      #   print
      #   sa_report_groups(total_cp,users,groups)

if __name__=="__main__":
   main(sys.argv[1:])
