#!/usr/bin/env python

import sys,commands,os,time,smtplib

# list of mail recipients
recipients=[]
mailhost="mx.test.org"

def mail(server=None,sender='',to='',subject='',text=''):
    headers="From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (sender,to,subject)
    session=smtplib.SMTP(server)
    session.sendmail(sender,to,headers+text)
    session.quit()

def mailing_list(recipients,title,msg=''):
   for each in recipients:
      mail(mailhost,"root@"+os.uname()[1],each,title,msg)

def poll_node(cmd_line,ret_type="Counter32:"):
   results=commands.getstatusoutput(cmd_line)
   if results[0]==0:
      parts=results[1].rsplit(ret_type)
      return float(parts[1])
   else:
      print "Error polling:",results[1] 
      return -1

def write_state(state_file,state):
   try:
      with open(state_file,'w') as f:
         f.write(str(state))
   except IOError:
      print "Error: failed to write '"+state_file+"'"
 
def read_state(state_file):
   try:
      with open(state_file,'r') as f:
         state=int(f.read())
   except IOError:
      write_state(state_file,0)
      state=0

   return state
 
def common_state(node,value,threshold,times_thresh,units=""):
   state_file="/tmp/"+node+".state"
   state=read_state(state_file)
   if value>=threshold:
      state+=1
      if state==times_thresh:
         mailing_list(recipients,"Over Limit: "+node+" @"+str(value)+units)

      write_state(state_file,state) # update state
   else:
      if state>2: # Must have been going for more than 1 poll previously
         write_state(state_file,0) # reset state
         mailing_list(recipients,"Under Limit: "+node+" @"+str(value)+units)
 
def main(argv):
   snmp_get="snmpget -v1 -c "
   cstring="default"  # Default community string
   times_thresh=3 # number of times over threshold to signal

   filer="filer" # Default filer to poll
   threshold=20000 # NFS ops threshold to signal on
   interval=5     # Default poll interval
   nfs_low_ops="1.3.6.1.4.1.789.1.2.2.6.0"

   head="cluster"
   load_thresh=4 # Linux load threshold to signal on
   load_1m="1.3.6.1.4.1.2021.10.1.3.1"

   # Poll cluster head node for 1m load
   cmd_line=snmp_get+cstring+" "+head+" "+load_1m
   head_load=poll_node(cmd_line,"STRING:")
   #print "head_load",head_load
   common_state(head,head_load,load_thresh,times_thresh)

   # Poll cluster file server for NFS IOPS
   cmd_line=snmp_get+cstring+" "+filer+" "+nfs_low_ops
   poll0=poll_node(cmd_line)
   if poll0>0:
      time.sleep(interval)
      poll1=poll_node(cmd_line)
      if poll1>0:
         nfs_ops=(poll1-poll0)/float(interval)
         #print "ops=",nfs_ops
         common_state(filer,nfs_ops,threshold,times_thresh," NFS ops/sec")

if __name__ == '__main__':
   main(sys.argv[1:])
