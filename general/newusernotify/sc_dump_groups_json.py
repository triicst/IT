#! /usr/bin/env python3

import sys, os, requests, csv, json, collections, subprocess

outfolder = '/var/www/toolbox'

def uniq(seq):
    """ remove duplicates from a list """ 
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())	

# Only works with Python3.5+
#ret = subprocess.call('getent group | grep _grp', stdout=subprocess.PIPE, 
#                   stderr=subprocess.PIPE, shell=True, universal_newlines=True)

ret = subprocess.check_output('getent group | grep _grp', shell=True, universal_newlines=True) 

groups={}
users={}
grouplines=ret.split('\n')
for groupline in grouplines:
	grouplist=groupline.split(':')
	if grouplist[0]!='':
		userlist=grouplist[-1].split(',')
		groups[grouplist[0]]=userlist
		for user in userlist:
			if user in users.keys():				
				users[user].append(grouplist[0])
			else:
				users[user] = [grouplist[0],]

j = json.dumps(groups, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/pi_groups.json', 'w') as f:
	f.write(j)

j = json.dumps(users, indent=4, default=lambda x:str(x))
with open(outfolder + '/json/pi_groupmember.json', 'w') as f:
	f.write(j)

sys.exit()
