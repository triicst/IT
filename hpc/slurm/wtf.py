#!/usr/bin/env python

import sys,getopt,commands,re,hostlist
from operator import itemgetter
from multiprocessing import Pool

# SNMP get command
# Assumption: all nodes have a common community string
snmp_get="snmpget -v1 "

# Default community string
cstring="phs"

def parse_proc_load(raw):
   results=re.findall('STRING: [0-9,.]+',raw)
   return float(results[0].split(' ')[1])

def query_node(node):
   results_dict={}

   results=commands.getstatusoutput(snmp_get+cstring+" "+node+
      " 1.3.6.1.4.1.2021.10.1.3.1")
   if results[0]==0:
      return([node,parse_proc_load(results[1])])
      #results_dict[node]=parse_proc_load(results[1])
   else:
      print "Error:",node+")",results[1]

   return [node,"Error!"]

def get_top_user(node):
   results=commands.getstatusoutput("nodetop "+node)
   if results[0]==0:
      for line in results[1].split('\n'):
         s_line=line.split()
         if len(s_line)==12 and s_line[0]!="PID":
            return [s_line[1],s_line[8],s_line[11]]
   else:
      print "Error:",node+")",results[1]

   return []

def print_report(nodelist,max_name_len,load_thr,guilty,reverse):
   for node in nodelist:
      if node[1]=="Error!":
         continue

      if reverse==True:
         if node[1]>=load_thr:
            continue
      elif node[1]<=load_thr:
         break

      if not guilty:
         print node[0].ljust(max_name_len),node[1]
      else:
         print node[0].ljust(max_name_len),node[1],
         blame=get_top_user(node[0])
         if blame:
            print blame[0],blame[1]+"%",blame[2]
         else:
            print

def parse_slurm_conf(slurm_conf_file,part):
   cluster=[]

   r_part=re.compile('PartitionName=(\S+).*?Nodes=(\S+)')
   r_node=re.compile("(?<=NodeName=)\S+")

   try:
      for line in open(slurm_conf_file,'r'):
         if line[0]!='#':
            m=r_node.search(line)
            if m:
               exp_nodelist=hostlist.expand_hostlist(m.group(0))
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

def max_name(x,y):
   if x>len(y[0]):
      return x
   else:
      return len(y[0])

def usage():
   print "wtf [options]"
   print "Options:"
   print "\t-t timeout"
   print "\t-n nodelist"
   print "\t-p partition"
   print "\t-c community_string"
   print "\t-l load_threshold"
   print "\t-g : print top user on each system"
   print "\t-L : invert load comparison"

def main(argv):
   global cstring
   global snmp_get

   # Initialize empty cluster list
   cluster_list=[]

   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"

   # Default load threshold to report
   load_thr=8.0

   guilty=False
   reverse=False

   # default to all nodes in configuration
   part=""

   # Default amount of parallelism
   workers=8

   try:
      opts,args=getopt.getopt(argv,"n:l:c:s:p:w:t:Lgh")
   except getopt.GetoptError:
      usage()
      sys.exit()

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-n"): # override default cluster file
         cluster_list=hostlist.expand_hostlist(arg)
      elif opt in ("-s"): # override default Slurm config file name
         slurm_conf=arg
      elif opt in ("-l"): # override default load level
         load_thr=float(arg)
         if load_thr<0:
            print "Error: invalid load level - "+arg+"!"
            sys.exit()
      elif opt in ("-c"): # override default community string
         cstring=arg
      elif opt in ("-g"): # print top user on each overused system
         guilty=True
      elif opt in ("-L"): # invert load comparison
         reverse=True
      elif opt in ("-w"): # invert load comparison
         workers=int(arg)
      elif opt in ("-t"): # timeout
         snmp_get+="-t "+arg+" "
      elif opt in ("-p"): # specify partition
         part=arg

   snmp_get+=" -c "

   if not cluster_list:
      cluster_list=parse_slurm_conf(slurm_conf,part)

   if not cluster_list:
      print "Error: no cluster nodes correspond to specification!" 
      sys.exit()

   pool=Pool(workers)
   results=pool.map(query_node,cluster_list) 
   pool.close()

   # sort results by load value and pass to report printer 
   print_report(sorted(results,key=itemgetter(1),reverse=True),
      reduce(max_name,results,0),load_thr,guilty,reverse)

if __name__=="__main__":
   main(sys.argv[1:])
