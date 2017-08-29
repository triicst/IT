#! /usr/bin/env python
"""
Application: Cifsblast
Version: 1.0
Requires: Unix (Linux, Solaris, Mac) OS, smbclient binary, Python 2.6+
Purpose: Generate a very high volume of CIFS write IO to stress networks and storage systems.
Author: Robert McDermott <rmcdermo@fhcrc.org>, Supriatno Agus <sagus@fhcrc.org>  
last updated: 2012-04-03
"""

import getpass
import sys
import os
import optparse
import random
import multiprocessing, Queue
import time


def main():
    # run
    # load up work queue

    print "\nAbout to blast %s with a total of %s jobs; %s jobs in parallel with a send buffer size of %s Bytes...\n" \
     % (opt.server, opt.num_jobs, opt.num_processes, opt.buffersize)
    print "Hit <ctrl>-c to stop\n"
    time.sleep(2)
    print "Creating task queue with a length of %s:" % opt.num_jobs 
    work_queue = multiprocessing.Queue()
    for job in range(opt.num_jobs):
        work_queue.put(job)
        print "---> adding task %s to queue" % job
 
    # create a queue to pass to workers to store the results
    result_queue = multiprocessing.Queue()
 
    # spawn workers
    print "Spawning %s concurrent workers:" % opt.num_processes
    for i in range(opt.num_processes):
        worker = Worker(work_queue, result_queue)
        # setting the daemon flag to True will make sure all children are killed with the parent
        worker.daemon = True
        worker.start()
        print "-->PID: %s" % worker.pid
 
    # collect the results off the queue
    results = []
    for i in range(opt.num_jobs):
        print "elapsed task time: %s" % result_queue.get()

class Worker(multiprocessing.Process):
 
    def __init__(self, work_queue, result_queue):
 
        # base class initialization
        multiprocessing.Process.__init__(self)
 
        # job management stuff
        self.work_queue = work_queue
        self.result_queue = result_queue
        self.kill_received = False
 
    def run(self):
        while not self.kill_received:
 
            # get a task
            #job = self.work_queue.get_nowait()
            print "%s tasks waiting in the queue" % self.work_queue.qsize()
            try:
                job = self.work_queue.get_nowait()
            except Queue.Empty:
                break
 
            # the actual processing
            print("Starting task %s..." % job)
            start = time.time()
            os.system('%s %s -U %s -c "iosize %s; recurse; prompt; cd %s; lcd %s; mput %s" > /dev/null 2>&1' \
              % (smb, opt.server, username, opt.buffersize, opt.remotedir, ldir, folder))
            elapsed = time.time() - start
            # store the result
            self.result_queue.put(elapsed)

if __name__ == "__main__":
    smb = '/usr/bin/smbclient'

    usage_ = "usage: %prog --server=//server/share --username=DOMAIN/username\
      --localdir=dir --remotedir=dir --jobs=integer (defaults to 100) --threads=integer\
      (defaults to system CPU core count + 2 ) [--password=userpassword (optional)]\
      [--buffersize=bytes (min 16384, max 16776960, default 64512 (optional)]".replace('     ', ' ')

    p = optparse.OptionParser(usage=usage_, version="%prog 1.0") 

    p.add_option('-s', '--server',  action='store', type='string', dest='server',\
     help='The CIFS server and share you want to use.')

    p.add_option('-u', '--username',  action='store', type='string', dest='username',\
     help='The username to connect with; format DOMAIN/username.')

    p.add_option('-p', '--password',  action='store', type='string', dest='password',\
     help='The provided users password. Optional; if not provided you\'ll be prompted for the password')

    p.add_option('-l', '--localdir',  action='store', type='string', dest='localdir',\
     help='The local directory to copy to the server.')

    p.add_option('-r', '--remotedir',  action='store', type='string', dest='remotedir',\
     help='The local directory to copy to the server.')

    p.add_option('-j', '--jobs',  action='store', type='int', dest='num_jobs',\
     help='The total number of copy jobs to run; requires a integer. Defaults to 100 jobs.')

    p.add_option('-t', '--threads',  action='store', type='int', dest='num_processes',\
     help='The total number of parallel jobs to run; requires a integer; defaults to the number of CPU\
     cores in the system + 2.')

    p.add_option('-b', '--buffersize',  action='store', type='long', dest='buffersize',\
     help='Smbclient uses an internal memory buffer by default of size 64512 bytes. This command allows this\
     size to be set to any range between 16384 bytes (16KB) and 16776960 bytes (64MB) (Optional).')

    cpus = multiprocessing.cpu_count() + 2
    p.set_defaults(num_processes=cpus, num_jobs=100, buffersize=64512)
    opt, args = p.parse_args()

    if len(sys.argv) < 5:
        p.error('use --help for usage information.')

    if opt.buffersize < 16384 or opt.buffersize > 16776960:
        p.error('--buffersize must be between 16384 and 1677690 Bytes, default size is 64512 Bytes')
    
    if not opt.password:
        password = getpass.getpass('Enter password for %s:' % opt.username)
        username = '%s%%%s' % (opt.username, password)
    else:
        username = '%s%%%s' % (opt.username, opt.password)

    if '/' in opt.localdir:
        local = opt.localdir.split('/')
        ldir = '/'.join(local[:-1])
        folder = local[-1]
    else:
        ldir = '.'
        folder = opt.localdir 

    main()
