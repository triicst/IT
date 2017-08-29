#!/usr/bin/env python3
"""
WTB - Where's The Beef? - returns list of cluster nodes sorted by free CPU/RAM
Jeff Katcher/FHCRC

Interesting MIB variables
(From UCD-SNMP-MIB)
memTotalReal.0 memAvailReal.0 
- don't know if I even need the total
(From HOST-RESOURCES-MIB)
hrProcessorTable
   hrProcessorEntry
      hrProcessorFrwID
      hrProcessorLoad # doesn't work under Solaris 10

.1.3.6.1.4.1.2021.10.1.3.1 = 1-minute system load
"""

# Template for Cluster Load Utility
import subprocess,sys,operator,re,os
from optparse import OptionParser

# Default filename for list of nodes
def_cluster_files=["~/wtb_nodelist","/usr/local/etc/wtb_nodelist"]
# Default community string
def_cstring="phs"

# SNMP get command 
# Assumption: all nodes have a common community string
snmp_get="snmpget -v1 -c "
snmp_walk="snmpwalk -v1 -c "

def delete_duplicates(list):
   keys={}
   for i in list:
      keys[i]=0
   return keys.keys()

# skip comment lines and ignore comments after nodenames
def build_nodelist(filenames):
   max_len=0
   nodelist=[]
   for filename in filenames:
      try:
         if filename[0]=='~':
            filename=filename.replace('~',os.path.expanduser("~"),1) 

         for line in open(filename,'r'):
            if line[0]!='#':
               node=line.strip().split(' ',1)[0]
               cur_len=len(node)
               if cur_len>0:
                  nodelist.append(node)
                  if cur_len>max_len:
                     max_len=cur_len
      except IOError:
#        print("Warning: cannot open nodefile '%s'" % filename)
         pass

   return max_len,delete_duplicates(nodelist)

# if list of returns, sum them assuming caller knows they're same type
def validate_snmp_int(s):
   sum=-1
   parts=s.rsplit("INTEGER: ")
   if len(parts)>1:
      for part in parts:
          if part[0].isdigit():
             sum+=int(part.split()[0])

   return sum

def validate_snmp_str(s):
   parts=s.rsplit("STRING:")
   if len(parts)==2: # strip leading space and extract # from '# kb' case
      return parts[1].rsplit('\\')[0].strip().split(' ')[0]
   else:
      return "(invalid)"

def parse_proc_load(raw):
   results=re.findall('INTEGER: [0-9]+',raw)
   free=0
   cpus=0
   for proc in results:
      if int(proc.split(' ')[1])<=1:
         free+=1
      cpus+=1
   return [free,cpus]

def run_cmd(cmdline):
   status=0
   try: 
      results=subprocess.check_output(cmdline,shell=True)
   except subprocess.CalledProcessError:
      results=""
      status=-1

   return status,str(results)

def query_nodes(nlist,cstring):
   nodelist=[]
   for node in nlist:
      status,results=run_cmd(snmp_get+cstring+" "+node+
         " memAvailReal.0 memBuffer.0 memCached.0")
      if status==-1:
         continue 
 
      free_mem=validate_snmp_int(results)
      if free_mem!=-1:
         status,results=run_cmd(snmp_walk+cstring+" "+node+
            " hrProcessorLoad")
         if status==-1:
            continue

         nodeinfo=[node,free_mem]
         nodeinfo.extend(parse_proc_load(results))

         status,results=run_cmd(snmp_get+cstring+" "+node+
            " .1.3.6.1.4.1.2021.10.1.3.1")
         if status==-1:
            continue

         # process load as float, though returned as string
         nodeinfo.append(float(validate_snmp_str(results)))

         nodelist.append(nodeinfo)

   return nodelist

# format cpu portion of report - SNMP query invalid if ncpu==0
def valid_cpus(fcpu,ncpu):
   if ncpu==0:
      results="can't query"
   else:
      results="%2d/%2d cpu%s" % (fcpu,ncpu,'s' if ncpu>1 else '')
   return '\t'+results+' avail\t'

def format_bytes(bytes):
   if bytes<1000:
      return "%d KB" % bytes
   else:
      bytes=bytes/1000
      if bytes<1000:
         return "%.2f MB" % bytes
      else:
         return "%.2f GB" % (bytes/1000)

def print_report(results,options,max_len):
   if options.memory==True:
      results.sort(key=lambda x:x[1],reverse=True)
   else:
      results.sort(key=lambda x:(x[2]/x[3],x[1]),reverse=True)

   if options.summary==None:
      for item in results:
         print(item[0].ljust(max_len)+valid_cpus(item[2],item[3])+format_bytes(item[1])+" avail\tload=%.2f" % item[4])
   else:
      for item in results:
         print(item[0]+' ',end='')
      print()

# main code begins here
def main(cluster_files=def_cluster_files,cstring=def_cstring):
   parser=OptionParser()
   parser.add_option("-m","--memory",action="store_true",
      help="sort by free memory instead of free CPUs")
   parser.add_option("-c","--cstring",
      help="SNMP community string (default="+def_cstring+")")
   parser.add_option("-f","--file",
      help="file containing list of nodes (default="+str(def_cluster_files)+")")
   parser.add_option("-s","--summary",action="store_true",
      help="show only ordered list of nodes")
   (options,args)=parser.parse_args()

   if options.file!=None:
      cluster_files=[options.file]

   if options.cstring!=None:
      cstring=options.cstring

   max_len,nodelist=build_nodelist(cluster_files)
   if len(nodelist)>0:
      results=query_nodes(nodelist,cstring)
      print_report(results,options,max_len)
   else:
      print("Error: no nodes in list!")

if __name__=="__main__":
   sys.exit(main())
