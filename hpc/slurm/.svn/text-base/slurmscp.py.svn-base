#!/usr/bin/env python

import sys,getopt,commands,hostlist

# strncmp analog
def strsubcmp(src,sub):
   return sub in src[:len(sub)]

def parse_slurm_conf(slurm_conf_file):
   cluster=[]

   try:
      for line in open(slurm_conf_file,'r'):
         if strsubcmp(line,"NodeName="):
            nodes=line.split()[0].split('=')[1]
            cluster.extend(hostlist.expand_hostlist(nodes))

   except IOError:
      print "Error: cannot open Slurm conf file at",slurm_conf_file

   return cluster

def usage():
   print "slurmssh [nodelist_pattern] from to"

def main(argv):
   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"

   argc=len(argv)
   if argc<2 or argc>3:
      usage()
   else:
      if argc==2:
         nodes=parse_slurm_conf(slurm_conf)
      else:
         nodes=hostlist.expand_hostlist(argv[0])

      if len(nodes)>0:
         for node in nodes:
            cmdline="scp "+argv[argc-2]+" "+node+":"+argv[argc-1]
            print "Running",cmdline
            results=commands.getstatusoutput(cmdline)
            if results[0]==0:
               print "OK",results[1]
            else:
               print "Error:",node+")",results[1]
      else:
         print "Error: empty or invalid list of cluster nodes!"

if __name__=="__main__":
   main(sys.argv[1:])
