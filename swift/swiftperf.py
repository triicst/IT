#!/usr/bin/env python3

import argparse
import random
import os
import socket
import datetime

import swiftclient

def create_test_data(size):
    dna='AGTC'
    test_data=''

    for i in range(size):
        test_data+=random.choice(dna)

    return test_data

def create_sw_conn(hostname=""):
    swift_auth_token=os.environ.get("OS_AUTH_TOKEN")
    storage_url=os.environ.get("OS_STORAGE_URL")

    if swift_auth_token and storage_url:
        return swiftclient.Connection(preauthtoken=swift_auth_token,
            preauthurl=storage_url)

    swift_auth=os.environ.get("ST_AUTH")
    swift_user=os.environ.get("ST_USER")
    swift_key=os.environ.get("ST_KEY")

    if swift_auth and hostname:
        swift_auth="https://"+hostname+"/auth/v1.0"

    if swift_auth and swift_user and swift_key:
        return swiftclient.Connection(authurl=swift_auth,user=swift_user,
            key=swift_key)

    print("Error: Swift environment not configured!")
    sys.exit()

def run_test(parse_args,hostname,test_data):
    start_time=datetime.datetime.now()
    sc=create_sw_conn(hostname)    
    if sc:
        create_sw_time=datetime.datetime.now()

        sc.put_object(parse_args.container,parse_args.object,test_data)
        put_time=datetime.datetime.now()

        headers,body=sc.get_object(parse_args.container,parse_args.object)
        get_time=datetime.datetime.now()

        sc.delete_object(parse_args.container,parse_args.object)
        delete_time=datetime.datetime.now()

        sc.close()

    with open(parse_args.file,'a') as f:
        if hostname=='':
            hostname=socket.gethostname()
        print("%s,%s,%s,%s,%s,%s" % 
            (start_time,hostname,create_sw_time-start_time,
                put_time-create_sw_time,get_time-put_time,
                delete_time-put_time),file=f)

def load_nodefile(nodefile):
    lines=[]
    try:
        with open(nodefile,'r') as f:
            lines=f.read().splitlines()
    except:
        print("Error: cannot read nodes from",nodefile)

    return lines

def run_tests(parse_args):
    test_data=create_test_data(parse_args.size)

    if parse_args.nodelist:
        nodes=load_nodefile(parse_args.nodelist)
        for node in nodes:
            run_test(parse_args,node,test_data)
    else:
        while True:
            run_test(parse_args,'',test_data)

# argparse config garbage
def parse_arguments():
    parser=argparse.ArgumentParser(
        description="Repeatedly get/put/delete objects to measure performance")
    parser.add_argument("-C","--container",help="destination container",
        type=str,required=True)
    parser.add_argument("-f","--file",help="name of output file",
        type=str,default='swiftperf.out')
    parser.add_argument("-n","--nodelist",help="file with list of swift nodes",
        type=str)
    parser.add_argument("-o","--object",help="name of test object",
        type=str,default='swiftperf')
    parser.add_argument("-s","--size",help="size of test object",
        type=int,default=1048576)

    return parser.parse_args()

def main():
    run_tests(parse_arguments())

if __name__ == '__main__':
    main()
