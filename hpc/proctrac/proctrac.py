#! /usr/bin/env python3

import os, sys, psutil, time

for i in range(10):
    for pid in psutil.pids():
        try:
            p=psutil.Process(pid)
            if p.username() != 'root' and p.status() != psutil.STATUS_ZOMBIE:
                print(p.username(),'|'," ".join(p.cmdline()),'|',p.cwd(),'|',p.io_counters(),'|',p.open_files())
        except:
            print("error")
    time.sleep(5)

