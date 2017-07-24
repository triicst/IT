#!/usr/bin/env python3

# Tonton Macoute: tracks and hopefully controls zombie procs

import os,sys,pwd

def add_pid(uids,uid,procname,ppid):
   if uid not in uids:
      uids[uid]={ppid:{procname:1}}
   else:
      if ppid in uids[uid]:
         if procname in uids[uid][ppid]:
            uids[uid][ppid][procname]=uids[uid][ppid][procname]+1
         else:
            uids[uid][ppid][procname]=1
      else:
         uids[uid][ppid]={procname:1}

def get_proclist():
   uids={}

   for pid in [pid for pid in os.listdir('/proc') if pid.isdigit()]:
      try:
         procname=''
         ppid=''

         for line in open(os.path.join('/proc',pid,'status'),'r'):
            if line.startswith('Name:'):
               procname=line.split()[1]
               continue

            if line.startswith('State:'):
               if line.split()[1]=='Z':
                  continue
               break

            if line.startswith('PPid:'):
               ppid=line.split()[1]
               continue

            if line.startswith('Uid:'):
               uid=int(line.split()[1])
               add_pid(uids,uid,procname,ppid)
               break

      except IOError: # proc already terminated
         continue

   return uids

def gen_report(uids):
   for uid,value in uids.items():
      for ppid,pidinfo in value.items():
          print(pwd.getpwuid(uid).pw_name,ppid,end='')
          for procname,count in pidinfo.items():
             print(" %s(%d)" % (procname,count),end='')
          print()

def main(argv):
   uids=get_proclist()
   gen_report(uids)

if __name__ == '__main__':
   main(sys.argv[1:])
