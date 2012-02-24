#!/usr/bin/env python

import sys,getopt,commands,os,re,hostlist,smtplib

recipients=[]
mailhost="mx.test.org"

def parse_slurm_conf_cores(line,nodelist,node_dict):
   s=re.search("Sockets=(\S+)",line)
   if s:
      cores=int(s.group(1))
      s=re.search("CoresPerSocket=(\S+)",line)
      if s:
         cores*=int(s.group(1))

   for node in nodelist:
      node_dict[node]=cores

def parse_slurm_conf(slurm_conf_file,part,node_dict):
   cluster=[]

   r_part=re.compile('PartitionName=(\S+).*?Nodes=(\S+)')
   r_node=re.compile("(?<=NodeName=)\S+")

   try:
      for line in open(slurm_conf_file,'r'):
         if line[0]!='#':
            m=r_node.search(line)
            if m:
               exp_nodelist=hostlist.expand_hostlist(m.group(0))
               parse_slurm_conf_cores(line,exp_nodelist,node_dict)
               if not part:
                  cluster.extend(exp_nodelist)
            elif part:
               m=r_part.search(line)
               if m and m.group(1) in part:
                  cluster.extend(hostlist.expand_hostlist(m.group(2)))
                  if len(part)==1:
                     break

   except IOError:
      print "Error: cannot open Slurm conf file at",slurm_conf_file

   return cluster

def get_total_cores(slurm_conf,part):
   slurm_node_dict={}

   int_part_list=parse_slurm_conf(slurm_conf,part,slurm_node_dict)
   if len(int_part_list)==0:
      print "Error: no nodes found in partition(s)!"
      sys.exit()

   return sum(map(lambda x:slurm_node_dict[x],int_part_list))

def parse_squeue(part,user,task_re,job_state):
   cmd_line="squeue -h -a -o \"%.7i %.9P %.8j %.8u %.2t %.10M %.6D %R %C\""
   user_dict={}

   results=commands.getstatusoutput(cmd_line)
   if results[0]==0:
      sqlines=results[1].split('\n')
      for sqline in sqlines:
         sqfields=sqline.split()
         if len(sqfields)==9 and (not part or sqfields[1] in part) and \
            (not user or sqfields[3] in user) and sqfields[4] in job_state and \
            (not task_re or task_re.search(sqfields[2])):
            node_cores=int(sqfields[8])
            if sqfields[3] not in user_dict:
               user_dict[sqfields[3]]=node_cores
            else:
               user_dict[sqfields[3]]+=node_cores
   else:
      print "Error:",results[1]

   return user_dict

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

def nodes_to_state(nodes,thresh):
   if nodes<=0:
      state=0 # red
   elif nodes<=thresh:
      state=1 # yellow
   else:
      state=2 # green

   return state

def report(user_dict,format,total,users,slurm_conf,parts):
   output="User, Cores\n"
   used=0
   free=-1

   for user in sorted(user_dict.items(),key=lambda user:user[1],reverse=True):
      output+=format % (user[0],user[1])
      used+=user[1]
   if total and not users:
      total_cores=get_total_cores(slurm_conf,parts)
      free=total_cores-used
      output+=format % ("Free",free)
   output+=format % ("Total",total_cores)

   return free,output

def usage():
   print "hitparade [-p partition][-u user][-t task_re]"

def main(argv):
   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"

   state_file="/tmp/hitparade.dat"
   gstate=["red","yellow","green"]

   try:
      opts,args=getopt.getopt(argv,"p:u:t:wfnch")
   except getopt.GetoptError:
      usage()
      sys.exit()

   parts=[]
   users=[]
   task_re=""
   job_state=["R","CG"]
   output="%10s %d\n"
   total=1
   notify=0

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-p"):
         parts.extend(arg.split(','))
      elif opt in ("-u"):
         users.extend(arg.split(','))
      elif opt in ("-t"):
         task_re=re.compile(arg)
      elif opt in ("-w"):
         job_state=["PD","S"]
      elif opt in ("-f"):
         total=0
      elif opt in ("-c"):
         output="%s,%d\n"
      elif opt in ("-n"):
         notify=1

   user_dict=parse_squeue(parts,users,task_re,job_state)

   # print only number if only one user is specified
   if users and len(users)==1:
      items=user_dict.items()
      if len(items):
         print user_dict.items()[0][1]
      else:
         print 0
   else:
      free,result=report(user_dict,output,total,users,slurm_conf,parts)
      if notify==1:
         last_state=read_state(state_file)
         new_state=nodes_to_state(free,8)
         if new_state!=last_state:
            write_state(state_file,new_state)
            mailing_list(recipients,"Hitparade State Change: "+
               gstate[new_state],result)
      else:
         print result


if __name__ == '__main__':
   main(sys.argv[1:])
