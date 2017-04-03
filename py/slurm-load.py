#! /usr/bin/env python

import subprocess, pandas

featurefilter='campus'
partitionfilter='campus'

squeuecmd = ['squeue', '--format=%i;%t;%D;%C;%a;%u']
sinfocmd = ['sinfo', '--format=%n;%c;%m;%f']

if partitionfilter != '':
    squeuecmd.append('--partition=%s' % partitionfilter)

squeue = subprocess.Popen(squeuecmd, stdout=subprocess.PIPE)
sinfo = subprocess.Popen(sinfocmd, stdout=subprocess.PIPE)

jobs=pandas.read_table(squeue.stdout, sep=';')
nodes=pandas.read_table(sinfo.stdout, sep=';')
if featurefilter != '':
    nodes = nodes[(nodes['FEATURES'].str.contains(featurefilter))]

# print(jobs.groupby(["ST"]).sum()["CPUS"])
# squeuehead = subprocess.Popen(['head',], stdin=squeue.stdout, stdout=subprocess.PIPE)

print(jobs.groupby(["ACCOUNT","USER"]).sum()["CPUS"])

print('\n CPU core Inventory:')
print('Total:', nodes.sum()["CPUS"])
print('Running:', jobs[jobs['ST'] == 'R'].sum()["CPUS"])
print('Pending:', jobs[jobs['ST'] == 'PD'].sum()["CPUS"])
