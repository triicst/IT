#!/usr/bin/env python2.6

import sys,getopt,commands,os,smtplib,time,datetime

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

def poll_ldap(ldap_server,canary_user):
   result=-2

   cmd_line="ldapsearch -h %s -x -b 'dc=local' '(cn=%s)'|grep numEntries" % (ldap_server,canary_user)
   results=commands.getstatusoutput(cmd_line)
   if results[0]==0:
      # looking for "# numEntries: 1"
      if "numEntries" in results[1]:
         num_entries=results[1].split(':')[1]
         if num_entries>=1:
            result=0
   else:
      print "ldapmod error:",results[1]
      result=-1

   return result

def try_polls(max_tries,try_delay,poll_func,poll_func_param1,poll_func_param2):
   poll_success=-1
   for tries in range(0,max_tries):
      if poll_func(poll_func_param1,poll_func_param2)==0:
         poll_success=0
         break
      time.sleep(try_delay)

   return poll_success

def restart_ldap():
   cmd_line="/etc/rc.d/ldap restart"
   results=commands.getstatusoutput(cmd_line)
   print results
   return results[0]

def usage():
   print "ldapmon.py [-l ldap_server][-t max_tries][-d max_delay]"

def main(argv):
   canary_user="petersen"
   ldap_server="localhost"
   state_file="/tmp/ldapmod.dat"
   lock_file="/tmp/ldapsync.LOCK"
   max_tries=3
   try_delay=30

   try:
      opts,args=getopt.getopt(argv,"l:t:d:h")
   except getopt.GetoptError:
      usage()
      sys.exit()

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-l"):
         ldap_server=arg
      elif opt in ("-t"):
         max_tries=int(arg)
      elif opt in ("-d"):
         try_delay=int(arg)

   if os.path.exists(lock_file):
      now=datetime.datetime.now()
      print str(now)+": LDAP update cycle in progress"
      sys.exit()

   last_state=read_state(state_file)

   if try_polls(max_tries,try_delay,poll_ldap,ldap_server,canary_user)==-1:
      msg="LDAP server failed %d polls\n" % max_tries
      if last_state>=0:
         if ldap_server=="localhost":
            msg+="Trying restart..."
            if restart_ldap()==0:
               if try_polls(max_tries,try_delay,poll_ldap,ldap_server)==0:
                  msg+="success!\n"
                  write_state(state_file,0)
               else:
                  msg+="failed repoll!\n"
                  write_state(state_file,-2)
            else:
               msg+="failed restart!\n"
               write_state(state_file,-1)

            ldap_server=os.uname()[1]
         else:
            write_state(state_file,last_state+1)

      if last_state>=0 and last_state<max_tries:
         mailing_list(recipients,"LDAP Monitor Event - %s" % ldap_server,msg)
   else:
      if last_state!=0:
         write_state(state_file,0)

if __name__ == '__main__':
   main(sys.argv[1:])
