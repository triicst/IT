#! /usr/bin/env python3

"""
checking for new scicomp users 
"""

import sys, os, json, requests, datetime

# get current list of scicomp users from https://lists.fhcrc.org/mailman/roster/scicomp-announce 
scusers = ["user1", "user2", "user3"]

# the user database of potential scientific computing users
j = requests.get('https://toolbox.fhcrc.org/json/sc_users.json').json()

lst =[]
for item in j:
    # check if hireDate is later than a certain date 
    if datetime.datetime.strptime(item['hireDate'], '%Y-%m-%dT%H:%M:%S') >= datetime.datetime(2016, 1, 1):
        # print(item['uid'], item['employeeID'])
        # select only hutch staff 
        if item['paygroup'] == "FHC":
            if item['uid'] in scusers:
                lst.append(item['mail'].strip())

print(lst)
