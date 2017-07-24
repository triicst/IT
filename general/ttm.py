#!/usr/bin/env python3

# Tonton Macoute: tracks and hopefully controls zombie procs

import os,sys,pwd

def get_proclist():
   uids={}

   for pid in [pid for pid in os.listdir('/proc') if pid.isdigit()]:
      try:
         procname=''
         ppid=''

         status=open(os.path.join('/proc',pid,'status'),'r')
         for line in status:
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
               if uid not in uids:
                  uids[uid]=[[pid,procname,ppid]]
               else:
                  uids[uid].append([pid,procname,ppid])

      except IOError: # proc already terminated
         continue

   return uids

def gen_ppid_report(pids):
   ppids={}

   for pid in pids:
      if pid[2] not in ppids:
         ppids[pid[2]]=[pid[0],pid[1]]
      else:
         ppids[pid[2]].append([pid[0],pid[1]])

   return ppids

def gen_report(uids):
   for uid,value in uids.items():
      ppids=gen_ppid_report(value)
      for ppid,pids in ppids.items():
          print(pwd.getpwuid(uid).pw_name,ppid,len(pids))

def main(argv):
   uids=get_proclist()
   gen_report(uids)

if __name__ == '__main__':
   main(sys.argv[1:])
