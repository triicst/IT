#!/usr/bin/env python
"""
WTF - Where's The Beef? - returns list of cluster nodes sorted by free CPU/RAM
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
import commands,sys,operator,re,os
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
#        print "Warning: cannot open nodefile '"+filename+"'"
         pass

   return max_len,delete_duplicates(nodelist)

def validate_snmp_int(s):
   parts=s.rsplit("INTEGER:")
   if len(parts)==2: # strip leading space and extract # from '# kb' case
      return int(parts[1].strip().split(' ')[0])
   else:
      return -1

def validate_snmp_str(s):
   parts=s.rsplit("STRING:")
   if len(parts)==2: # strip leading space and extract # from '# kb' case
      return parts[1].strip().split(' ')[0]
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

def query_nodes(nlist,cstring):
   nodelist=[]
   for node in nlist:
      # grab available free memory
      results=commands.getstatusoutput(snmp_get+cstring+" "+node+
         " memAvailReal.0")
      if results[0]==0:
         free_mem=validate_snmp_int(results[1])
         if free_mem!=-1:
            results=commands.getstatusoutput(snmp_walk+cstring+" "+node+
               " hrProcessorLoad")
            if results[0]==0:
               nodeinfo=[node,free_mem]
               nodeinfo.extend(parse_proc_load(results[1]))
             
               results=commands.getstatusoutput(snmp_get+cstring+" "+node+
                  " .1.3.6.1.4.1.2021.10.1.3.1")
               if results[0]==0:
                  nodeinfo.append(validate_snmp_str(results[1]))

               nodelist.append(nodeinfo)
            else:
               print node+") "+results[1]
         else:
            print node+") "+results[1]
      else:
         print node+") "+results[1]
   return nodelist

# format cpu portion of report - SNMP query invalid if ncpu==0
def valid_cpus(fcpu,ncpu):
   if ncpu==0:
      results="unavailable"
   else:
      results=str(fcpu)+"/"+str(ncpu)+" cpu"
      if ncpu>1:
         results=results+'s'
   return '\t'+results+' avail \t'

def multicmp(x,y,key1,key2,key3):
   result=cmp(x[key1],y[key1])
   if result==0 and float(y[key3])>0:
      result=cmp(float(x[key2])/float(x[key3]),float(y[key2])/float(y[key3]))
   return result

# total kludge to sort by ratio
def multicmp2(x,y,key1,key2,key3):
   if float(y[key3])==0 or float(x[key3])==0:
      result=0
   else:
      result=cmp(float(x[key1])/float(x[key3]),float(y[key1])/float(y[key3]))

   if result==0:
      result=cmp(x[key2],y[key2])
   return result

def format_bytes(bytes):
   if bytes<1000:
      return str(bytes)+" KB"
   else:
      bytes=bytes/1000
      if bytes<1000:
         return str(bytes)+" MB"
      else:
         return str(bytes/1000)+" GB"

def print_report(results,key1,key2,key3,max_len,summary):
   if key1==2: # sort by cpu
      results.sort(lambda x,y:multicmp2(y,x,key1,key2,key3))
   else:
      results.sort(lambda x,y:multicmp(y,x,key1,key2,key3))

   if summary==None:
      for item in results:
         print item[0].ljust(max_len)+valid_cpus(item[2],item[3])+format_bytes(item[1])+" avail\tload="+item[4]
   else:
      for item in results:
         print item[0],

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
      if options.memory==True:
         print_report(results,1,2,3,max_len,options.summary) # field 1 is mem
      else:
         print_report(results,2,1,3,max_len,options.summary) # field 2 is cpu
   else:
      print "Error: no nodes in list!"

if __name__=="__main__":
   sys.exit(main())
