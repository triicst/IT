#!/usr/bin/env python

import sys,getopt,commands,hostlist,re
from multiprocessing import Pool

def parse_slurm_conf(slurm_conf_file,part=""):
   cluster=[]
   if part:
      r=re.compile('PartitionName=(\S+).*?Nodes=(\S+)')
   else:
      r=re.compile("(?<=NodeName=)\S+")

   try:
      for line in open(slurm_conf_file,'r'):
         if line[0]!='#':
            m=r.search(line)
            if m:
               if part:
                  if part==m.group(1):
                     return hostlist.expand_hostlist(m.group(2))
               else:
                  cluster.extend(hostlist.expand_hostlist(m.group(0)))
   except IOError:
      print "Error: cannot open Slurm conf file at",slurm_conf_file

   return cluster

def copy_to_node(cmdline):
   #print cmdline[1]
   results=commands.getstatusoutput(cmdline[1])
   if results[0]==0:
      return "OK"
   else:
      return "Error:"+cmdline[0]+") "+results[1]

def usage():
   print "slurmscp [options] [nodelist_pattern] from to"
   print "Options:"
   print "\t-p partition : connect to all nodes in partition"
   print "\t-n : dump nodelist"
   print "\t-N workers : number of parallel workers"

def main(argv):
   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"
   num_workers=8

   try:
      opts,args=getopt.getopt(argv,"p:nh")
   except getopt.GetoptError:
      usage()
      sys.exit()

   nodes=[]

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-p"): # partition
         nodes=parse_slurm_conf(slurm_conf,arg)
         if len(nodes)==0:
            print "Error: invalid partition -",arg
            sys.exit()
      elif opt in ("-n"): # dump nodelist
         if not nodes:
            nodes=parse_slurm_conf(slurm_conf)

         for node in nodes:
            print node
         sys.exit()
      elif opt in ('-N'): # set workers
         num_workers=int(arg)

   argc=len(args)
   if argc<2 or argc>3:
      usage()
   else:
      if argc==3:
         nodes=hostlist.expand_hostlist(args[0])
      elif not nodes:
         nodes=parse_slurm_conf(slurm_conf)

      if len(nodes)>0:
         cmdline=[]
         for node in nodes:
            cmdline.append([node,"scp "+args[argc-2]+" "+node+":"+args[argc-1]])

         pool=Pool(num_workers)
         results=pool.map(copy_to_node,cmdline)
         pool.close()

         for result in results:
            if result!="OK":
               print result
      else:
         print "Error: empty or invalid list of cluster nodes!"

if __name__=="__main__":
   main(sys.argv[1:])
