#!/usr/bin/env python

import sys,getopt,commands,hostlist,re,os,smtplib

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
               if m and m.group(1)==part:
                  return hostlist.expand_hostlist(m.group(2))

   except IOError:
      print "Error: cannot open Slurm conf file at",slurm_conf_file

   return cluster

def parse_squeue(node_dict,user_dict,part_name=""):
   cmd_line="squeue -h -a -o \"%.7i %.9P %.8j %.8u %.2t %.10M %.6D %R %C\""
   if part_name:
      cmd_line+=" -p "+part_name
   results=commands.getstatusoutput(cmd_line)
   if results[0]==0:
      sqlines=results[1].split('\n')
      for sqline in sqlines:
         sqfields=sqline.split()
         if sqfields[4] in ["R","CG"]: # if running
            node_cores=int(sqfields[8])
            node_dict[sqfields[7]][0]-=node_cores
            if sqfields[3] not in user_dict:
               user_dict[sqfields[3]]=[node_cores,[sqfields[7]]]
            else:
               user_dict[sqfields[3]][0]+=node_cores
               if sqfields[7] not in user_dict[sqfields[3]][1]:
                  user_dict[sqfields[3]][1].append(sqfields[7])
   else:
      print "Error:",results[1]

def poll_node(cmd_line,ret_type="Counter32:"):
   results=commands.getstatusoutput(cmd_line) 
   if results[0]==0:                          
      parts=results[1].rsplit(ret_type)       
      return float(parts[1])                  
   else:                                      
      print "Error polling:",results[1]       
      return -1      

def get_node_load(node):
   snmp_get="snmpget -v1 -c "
   cstring="phs"  # Default community string
   load_1m="1.3.6.1.4.1.2021.10.1.3.1"

   cmd_line=snmp_get+cstring+" "+node+" "+load_1m
   return poll_node(cmd_line,"STRING:")

def count_free_nodes(node_dict):
   free_nodes=0
   for node in node_dict.items():
      if node[1][0]==node[1][2]:
         free_nodes+=1

   return free_nodes

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

def nodes_to_state(nodes):
   if nodes<=0:
      state=0 # red
   elif nodes<=2:
      state=1 # yellow
   else:
      state=2 # green

   return state

def usage():
   print "grabby.py [-n (notification mode)][-p partition]"

def main(argv):
   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"
   int_part_name="pubint"

   state_file="/tmp/grabby.dat"
   gstate=["red","yellow","green"]

   slurm_node_dict={}
   node_dict={}
   user_dict={}

   try:
      opts,args=getopt.getopt(argv,"np:h")
   except getopt.GetoptError:
      usage()
      sys.exit()

   notify=0

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-n"):
         notify=1
      elif opt in ("-p"):
         int_part_name=arg

   int_part_list=parse_slurm_conf(slurm_conf,int_part_name,slurm_node_dict)
   if len(int_part_list)==0:
      print "Error: no members found in partition",int_part_name
   else:
      #print "Getting Loads"
      for node in int_part_list:
         cores=slurm_node_dict[node]
         node_dict[node]=[cores,get_node_load(node),cores]

      #print "Getting Users"
      parse_squeue(node_dict,user_dict,int_part_name)
      free_nodes=count_free_nodes(node_dict)

      if notify==1:
         last_state=read_state(state_file)
         new_state=nodes_to_state(free_nodes)
         if new_state==last_state:
            sys.exit()
         write_state(state_file,new_state)
      
      output="Node, Free Cores, Load\n"
      for node in sorted(node_dict.items(),key=lambda item:item[1][0],reverse=True):
         output+= "%s, %d, %.2f\n" % (node[0],node[1][0],node[1][1])

      output+="\n"

      output+="User, Cores, Node(s)\n"
      for user in sorted(user_dict.items(),key=lambda user:user[1][0],reverse=True):
         output+= "%s, %d, %s\n" % (user[0],user[1][0],hostlist.collect_hostlist(user[1][1]))

      if notify==1:       
         mailing_list(recipients,"Grabnode State Change: "+gstate[new_state],output)
      else:
         print output
 
if __name__ == '__main__':
   main(sys.argv[1:])
