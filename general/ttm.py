#!/usr/bin/env python3

# Tonton Macoute: tracks and hopefully controls zombie procs

import os,sys,pwd

def add_pid(uids,uid,pid_info,ppid):
   if uid not in uids:
      uids[uid]={ppid:pid_info}
   else:
      if ppid in uids[uid]:
         uids[uid][ppid].append(pid_info)
      else:
         uids[uid][ppid]=pid_info

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
               add_pid(uids,uid,[pid,procname],ppid)
               break

      except IOError: # proc already terminated
         continue

   return uids

def gen_report(uids):
   for uid,value in uids.items():
      for ppid,pids in value.items():
          print(pwd.getpwuid(uid).pw_name,ppid,len(pids))

def main(argv):
   uids=get_proclist()
   gen_report(uids)

if __name__ == '__main__':
   main(sys.argv[1:])
