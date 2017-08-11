#! /usr/bin/env python3

import sys, os, requests, csv, json, collections, subprocess

outfolder = '/var/www/toolbox'

ret = subprocess.run('getent group | grep _grp', stdout=subprocess.PIPE, 
                   stderr=subprocess.PIPE, shell=True, universal_newlines=True)

# print(ret.returncode, ret.stdout, ret.stderr)

groups={}
grouplines=ret.stdout.split('\n')
for groupline in grouplines:
    grouplist=groupline.split(':')
    if grouplist[0]!='':
        groups[grouplist[0]]=grouplist[-1].split(',')

j = json.dumps(groups, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/pi_groups.json', 'w') as f:
        f.write(j)

sys.exit()
