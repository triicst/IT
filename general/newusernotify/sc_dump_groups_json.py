#! /usr/bin/env python3

import sys, os, requests, csv, json, collections, subprocess

outfolder = '/var/www/toolbox'

# Only works with Python3.5+
#ret = subprocess.call('getent group | grep _grp', stdout=subprocess.PIPE, 
#                   stderr=subprocess.PIPE, shell=True, universal_newlines=True)

ret = subprocess.check_output('getent group | grep _grp', shell=True, universal_newlines=True) 

groups={}
grouplines=ret.split('\n')
for groupline in grouplines:
    grouplist=groupline.split(':')
    if grouplist[0]!='':
        groups[grouplist[0]]=grouplist[-1].split(',')

j = json.dumps(groups, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/pi_groups.json', 'w') as f:
        f.write(j)

sys.exit()
