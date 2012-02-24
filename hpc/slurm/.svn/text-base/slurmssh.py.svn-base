#!/usr/bin/env python

import sys,getopt,commands,hostlist,re,os

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

def parse_slurm_env(env_var_name):
   cluster=[]
   env=os.getenv(env_var_name)
   if env is not None:
      cluster.extend(hostlist.expand_hostlist(env))
   else:
      print "Error: cannot get "+env_var_name+" from environment"

   return cluster

def usage():
   print "slurmssh [options] [nodelist_pattern] command"
   print "Options:"
   print "\t-e : use list of nodes from Slurm environment"
   print "\t-A : pass agent forwarding flag to ssh"
   print "\t-p partition : connect to all nodes in partition"
   print "\t-n : dump nodelist"
   print "\t-B : break on error"

def main(argv):
   # Default slurm configuration
   slurm_conf="/etc/slurm/slurm.conf"

   try:
      opts,args=getopt.getopt(argv,"eAp:nBvh")
   except getopt.GetoptError:
      usage()
      sys.exit()

   cont_if_err=1
   slurm_env=False
   ssh_param=""
   nodes=[]

   debug=0

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-e"): # override default cluster file
         nodes=parse_slurm_env("SLURM_JOB_NODELIST")
         if len(nodes)==0:
            print "Error: No nodes in Slurm job nodelist!"
            sys.exit()
      elif opt in ("-A"): # pass ssh-agent forwarding flag to ssh
         ssh_param+="-A "
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
      elif opt in ("-B"): # break on error
         cont_if_err=0
      elif opt in ("-v"): # dump nodelist
         debug=1

   argc=len(args)
   if argc<1 or argc>2:
      usage()
   else:
      if len(nodes)==0:
         if argc==1:
            nodes=parse_slurm_conf(slurm_conf)
         else:
            nodes=hostlist.expand_hostlist(args[0])

      if len(nodes)>0:
         for node in nodes:
            print "Running on",node

            # switched to inferior os.system in case responses are required
            cmdline="ssh "+ssh_param+node+" '"+args[argc-1]+"'"
            if debug:
               print cmdline
            result=os.system(cmdline)
            if result!=0 and cont_if_err==0:
               print "ssh returns status",result
               break

            #results=commands.getstatusoutput(cmdline)
            #if results[0]==0:
            #   print results[1]
            #else:
            #   print "Error:",node+")",results[1]
      else:
         print "Error: empty or invalid list of cluster nodes!"

if __name__=="__main__":
   main(sys.argv[1:])
