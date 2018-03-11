#!/usr/bin/env python3
import os

"""
top - 10:16:21 up 71 days,  1:12, 62 users,  load average: 1.66, 1.85, 1.85
Tasks: 2303 total,   2 running, 1989 sleeping, 296 stopped,  16 zombie
%Cpu(s):  2.4 us,  0.3 sy,  0.1 ni, 97.2 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem:  39587244+total, 33480147+used, 61070960 free,   247632 buffers
KiB Swap: 11480984+total, 22013932 used, 92795920 free. 12432412+cached Mem

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
38525 agartlan  20   0 1261956 251216   6104 R  98.5  0.1   2353:42 python
50531 rmcdermo  20   0   24408   3180   1024 R  15.5  0.0   0:00.07 top
 2217 tholzman  20   0   16636   1080    684 S  10.4  0.0 243:34.38 sftp-server
"""

def main():
    users = {}
    ps = getprocs()
    for p in ps:
        try:
            if not p: continue
            pp = p.split()
            if pp[0].isnumeric():
                user = pp[1]
                cpu = float(pp[8])
                if user in users:
                    users[user] += cpu 
                else:
                    users[user] = cpu 
        except:
              continue
   
    rpt = [] 
    for u in sort_by_value(users)[::-1][:10]:
        if users[u] < threshold: continue 
        rpt.append("heavy_cpu_user{user=\"%s\"} %d" % (u, users[u]))
     
    if rpt:
        print("# TYPE heavy_cpu_user gauge")
        for r in rpt:
            print(r) 
    else:
        print("")

def getprocs():
    ps = os.popen("top -b -n 1").readlines()
    ps = [p.strip() for p in ps]
    return(ps) 


def sort_by_value(d):
    items=d.items()
    backitems=[ [v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))]

if __name__ == "__main__":
    threshold = 90 
    main()
