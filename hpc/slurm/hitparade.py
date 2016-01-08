#!/usr/bin/env python
"""
Show used and available public cores. Break down used
cores by user and account
"""
import sys
import os
import logging
import argparse
import csv
import pyslurm
import cmath
import pwd

ignorenodetypes = ['gizmoc', 'gizmod']

def main():
    """
    Do some stuff, eventually printing output to stdout...
    """
    # Parse command-line arguments
    arguments = parse_arguments()

    # Logging setup
    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)


    Nodes = pyslurm.node()
    node_dict = Nodes.get()
    Jobs = pyslurm.job()
    job_dict = Jobs.get()
    #print(job_dict)

    if len(node_dict) > 0 and len(job_dict) > 0:

        nt = get_nodetag(node_dict, job_dict, arguments)
        pc = get_pending(job_dict)

        if arguments.csv:
            print_csv(arguments.csv_header_suppress, nt, pc)
        else:
            js=get_aggregated_jobs(job_dict, arguments)
            print_usage(js)
            

    else:

        print "No Nodes and/or no Jobs found !"

    sys.exit()


    node_reservations = get_node_reservations()
    jobs = get_jobs(all_jobs=arguments.all_jobs)
    cred_totals, public_cores, public_nodes, public_nodes_free = get_counts(node_reservations, jobs)

    if arguments.free_cores:
        print_free_cores(cred_totals, public_cores)
    elif arguments.csv:
        print_csv(arguments.csv_header_suppress, cred_totals, public_cores, public_nodes, public_nodes_free)
    else:
        print_output(cred_totals, public_cores, public_nodes, public_nodes_free) 


def print_usage(ajobs):
    for k,v in sorted(ajobs.items()):
        print("\n === Queue: %s ======= (R / PD) %s" % (k, "="*(12-len(k))))
        tr=0
        tp=0
        #print('v:', v)
        for kk,vv in sorted( v.items(), key=lambda x: x[1], reverse=True):
            #print('vv:', vv)
            tr+=vv[0]
            tp+=vv[1]
            print ("{:>25} {:<5}".format( kk, "%s / %s" % (vv[0], vv[1])))
        if len(v)>1:
            print ("{:>25} {:<5}".format( "TOTAL:", "%s / %s" % (tr, tp)))
        

def get_aggregated_jobs(job_dict, arguments):
    # account, user_id, job_state, partition, num_cpus, num_nodes

    ajobs={}

    for key, value in job_dict.items():
        luser=pwd.getpwuid(value['user_id'])

        if arguments.pi:
            mykey = "%s" % value['account']
        else:
            mykey = "%s (%s)" % (value['account'], luser[0])
        if ajobs.has_key(value['partition']):
            udict = ajobs[value['partition']]
            if udict.has_key(mykey):
                ulist = udict[mykey]
            else:
                ulist = [0, 0]
        else:
            udict={}
            ulist = [0, 0]
            udict[mykey] = ulist             
        r=0
        p=0
        if value['job_state'] == 'RUNNING':
            r = value['num_cpus']
        elif value['job_state'] == 'PENDING':
            p = value['num_cpus']
        ulist[0]+=r
        ulist[1]+=p
        udict[mykey]=ulist
        ajobs[value['partition']]=udict

##        if value['job_state'] != 'RUNNING':                     
##            print('account: %s' % value['account'])
##            print('user_id: %s' % luser[0])
##            #print('job_state: %s' % (value['job_state'][0]))
##            print('job_state: %s' % value['job_state'])
##            print(value['job_state'])
##            if value['job_state'][0] == 2:
##                print('*') * 60
##            print('partition: %s' % value['partition'])
##            print('num_cpus: %s' % value['num_cpus'])
##            print('-') * 40
        
        
    return ajobs

def print_csv(csv_header_suppress, nodetags, pendingcores):
    """
    Display totals to stdout in csv format. Unless --all is used,
    preemptees are not included.
    """

##--------------------------------------------------------------------------------
##Feature: [Installed, Allocated, Offline, Idle, LOAD, Restart(of allocated)]
##--------------------------------------------------------------------------------
##Total: [2952, 2759, 96, 97, 'Load:2361', 1187]
##campus,restart,rx200: [108, 105, 0, 3, 'Load:106', 0]
##campus,restart,x10sle: [720, 638, 0, 82, 'Load:491', 0]
##--------------------------------------------------------------------------------

    # Header
    if not csv_header_suppress:
        csv.writer(sys.stdout).writerow(['label', 'cores_total', 'cores_pending', 
            'cores_idle', 'cores_used_restart', 'cores_used_priority', 'unix_load'])

    # 'campus - public cores'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]
    label = 'campus - public cores'
    for key, value in sorted(nodetags.iteritems()):
        if key.startswith('campus'):
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    if pendingcores.has_key('campus'):
        cores_pending = pendingcores['campus']
            
    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])

    # 'all - entire cluster'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]
    for k, v in pendingcores.iteritems():
        cores_pending+=v

    label = 'all - entire cluster'
    for key, value in sorted(nodetags.iteritems()):
        if key.startswith('Total'):
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])


    # 'full - public nodes'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]
    label = 'gizmog - subset of campus'
    if pendingcores.has_key('full'):
        cores_pending=pendingcores['full']
    
    for key, value in sorted(nodetags.iteritems()):
        if key.endswith(',gizmog'):
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])


    # 'grabnode - public nodes'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]
    label = 'grabnode - discontinued'
    for key, value in sorted(nodetags.iteritems()):
        if key.startswith('grabnode,'):         
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])


    # 'largenode - public cores'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]
    
    for key, value in sorted(nodetags.iteritems()):
        if key.endswith(',gizmoh'):
            label = 'largenode - gizmoh'
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])


    # 'private nodes'
    cores_total, cores_pending, cores_idle, cores_used_restart, cores_used_priority, unix_load = [0, 0, 0, 0, 0, 0]

    label = 'private nodes'
    for key, value in sorted(nodetags.iteritems()):
        if not key.startswith('largenode,') and not key.startswith('campus,') and \
            not key.startswith('full,') and not key.startswith('grabnode,') and \
            not key.startswith('Total'):
            cores_total+=value[0]-value[2]
            cores_idle+=value[3]
            cores_used_restart+=value[5]
            cores_used_priority+=value[1]-value[5]
            unix_load+=value[4]/100

    csv.writer(sys.stdout).writerow([label, cores_total, cores_pending, cores_idle,
                cores_used_restart, cores_used_priority, unix_load])


    
def get_pending(job_dict):
    """ 
    get dictionary of pending jobs by partition 
    """

    pendingcores={}

    for key1, value1 in job_dict.iteritems():
        if value1['job_state'] == 'PENDING':  # is the job pending
            pcores = int(value1['num_cpus'])
            if pendingcores.has_key(value1['partition']):
                pcores += pendingcores[value1['partition']]
            pendingcores[value1['partition']] = pcores

    return pendingcores


def get_nodetag(node_dict, job_dict, arguments):

    if node_dict and job_dict:

#       print "-" * 80

        nodetag={}
        nodetag["Total"] = [0,0,0,0,0,0]

        restartcores={}
        extrarestartcores=0 # multi node restart jobs cannot be easily assigned to a tag 

        for key1, value1 in job_dict.iteritems():

            if value1['job_state'] == 'RUNNING':  # is the job running
                if value1['partition'] == 'restart':
                    if int(value1['num_nodes']) > 1:
                        print("more than 1 node in restart job: adding restart cores only to Total!!!")
                        extrarestartcores += int(value1['num_cpus'])

                    else:
                        node = value1['nodes']
                        rcores=0
                        if restartcores.has_key(node):
                            rcores=restartcores[node]
                        restartcores[node]=rcores+int(value1['num_cpus'])

        for key, value in node_dict.iteritems():

            cont=0
            for typ in ignorenodetypes:
                if value['name'].startswith(typ):
                    cont=1
            if cont==1:
                continue

            cpuinst = value['cpus']
            #cpualloc = int(abs(cmath.sqrt(value['alloc_cpus'])))
            cpualloc = value['alloc_cpus']
            cpuoffline = 0
            cpuidle = cpuinst-cpualloc
            cpuload = value['cpu_load']
            cpurestart = 0
            if restartcores.has_key(value['name']):
                cpurestart = restartcores[value['name']]
            features = value['features']+','+value['name'][:6]
            ##print('state',value['state'][0])

            if value['cpu_load'] > 10000000:   # down or drained node
                cpuoffline = value['cpus']
                cpualloc = 0
                cpuidle = 0
                cpuload = 0
                cpurestart = 0


            if arguments.debug:
                print(value['name'],features,cpuinst,cpualloc,cpuidle,cpuload,cpurestart,value['state'])
            #sys.exit()

            if nodetag.has_key(features):
                nclass = nodetag[features]
                #print(features, nclass)
                nodetag[features]=[nclass[0]+cpuinst,nclass[1]+cpualloc,nclass[2]+cpuoffline,
                    nclass[3]+cpuidle,nclass[4]+cpuload,nclass[5]+cpurestart]
            else:
                nodetag[features]=[cpuinst,cpualloc,cpuoffline,cpuidle,cpuload,cpurestart]

            total = nodetag["Total"]
            
            nodetag["Total"]=[total[0]+cpuinst,total[1]+cpualloc,
                total[2]+cpuoffline,total[3]+cpuidle,total[4]+cpuload,total[5]+cpurestart]


        total = nodetag["Total"]
        total[5]+=extrarestartcores   # adding cores from multi-node restart jobs
        nodetag["Total"]=total  #
        #print(nodetag)
        return nodetag

def parse_arguments():
    """
    Gather command-line arguments.
    """

    parser = argparse.ArgumentParser(prog='hitparade.py',
        description='Show cluster users and basic usage stats for public ' + \
        'nodes and cores.')
    parser.add_argument( '--debug', '-d', action='store_true', default=False,
        help='Turn on debugging output.')
    parser.add_argument( '--all', '-a', dest='all_jobs', action='store_true', 
        help='Show all core usage.  If set, results will include preemptees',
        default=False )
    parser.add_argument( '--csv', '-c', dest='csv', action='store_true', 
        help='Output core and node totals to csv.',
        default=False )
    parser.add_argument( '--csv-header-suppress', '-s', dest='csv_header_suppress', 
        action='store_true', 
        help='Used with --csv, suppresses header. Default is False, show header.',
        default=False )
    parser.add_argument( '--pi', '-p', dest='pi', action='store_true', 
        help='Aggregate data by PI only.',
        default=False )
    parser.add_argument( '--free-cores', '-f', dest='free_cores', 
        action='store_true', 
        help='Print free cores and exit.',
        default=False )

    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main())
