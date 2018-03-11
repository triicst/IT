#!/usr/bin/env python3
import os


"""
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
rmcdermo 44501  0.0  0.0 178648  2472 ?        S    16:15   0:00 sshd: rmcdermo@pts/8
rmcdermo 44502  0.0  0.0  22244  5696 pts/8    Ss   16:15   0:00 -bash
rmcdermo 49191  0.0  0.0  16068  1232 pts/8    R+   16:32   0:00 ps ux
rmcdermo 56778  0.0  0.0  10616   676 ?        Ss    2017   0:00 ssh-agent -s
"""

def main():
    users = {}
    ps = getprocs()
    for p in ps:
        try:
            if p.startswith("USER"): continue
            pp = p.split()
            user = pp[0]
            rss = int(pp[5])
            if user in users:
                users[user] += rss
            else:
                users[user] = rss
        except:
              continue
    
    rpt = []
    for u in sort_by_value(users)[::-1][:10]:
        if users[u] < threshold: continue
        rpt.append("heavy_ram_user{user=\"%s\"} %d" % (u, users[u]))

    if rpt:
        print("# TYPE heavy_ram_user gauge")
        for r in rpt:
            print(r)
    else:
        print("")



def getprocs():
    ps = os.popen("/bin/ps aux").readlines()
    ps = [p.strip() for p in ps]
    return(ps) 


def sort_by_value(d):
    items=d.items()
    backitems=[ [v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))]

if __name__ == "__main__":
    threshold = 10485760
    main()
