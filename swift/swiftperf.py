#!/usr/bin/env python3

import argparse
import random
import os,sys
import socket
import datetime
import time

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

def td_sec(td):
    return td.total_seconds()

results=[]

def output_results(file,host,create,put,get,delete):
    global results

    if host=='':
        host=socket.gethostname()
    else:
        #print(host)
        results.append([host,create,put,get,delete])

    with open(file,'a') as f:
        print("%s,%f,%f,%f,%f" % (host,td_sec(create),td_sec(put),td_sec(get),
            td_sec(delete)),file=f)

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

    output_results(parse_args.file,hostname,
        create_sw_time-start_time,put_time-create_sw_time,get_time-put_time,
        delete_time-put_time)

def load_nodefile(nodefile):
    lines=[]
    try:
        with open(nodefile,'r') as f:
            lines=f.read().splitlines()
    except:
        print("Error: cannot read nodes from",nodefile)

    return lines

def print_report(results):
    notime=datetime.timedelta(0)
    low=[[notime,''],[notime,''],[notime,''],[notime,'']]
    high=[[notime,''],[notime,''],[notime,''],[notime,'']]
    total=[notime,notime,notime,notime]

    for result in results:
        for i in range(0,len(total)):
            if low[i][1]=='' or result[i+1]<low[i][0]:
                low[i]=[result[i+1],result[0]]
            if high[i][1]=='' or result[i+1]>high[i][0]:
                high[i]=[result[i+1],result[0]]
            total[i]+=result[i+1]

    i=0
    for item in ['connect','put','get','delete']:
        print("%s: low %f:%s high %f:%s avg %f" % (item,td_sec(low[i][0]),
            low[i][1],td_sec(high[i][0]),high[i][1],
            td_sec(total[i]/len(results))))
        i+=1

def run_tests(parse_args):
    global results

    test_data=create_test_data(parse_args.size)
    nodes=load_nodefile(parse_args.nodelist) if parse_args.nodelist else ['']

    while True:
        for node in nodes:
            run_test(parse_args,node,test_data)

        if parse_args.nodelist:
            print_report(results)
            results=[]

        if parse_args.iterations>0:
           parse_args.iterations-=1
        elif parse_args.iterations==0:
           break

        if parse_args.delay>0:
            time.sleep(parse_args.delay)

# argparse config garbage
def parse_arguments():
    parser=argparse.ArgumentParser(
        description="Repeatedly get/put/delete objects to measure performance")
    parser.add_argument("-C","--container",help="destination container",
        type=str,required=True)
    parser.add_argument("-f","--file",help="name of output file",
        type=str,default='swiftperf.csv')
    parser.add_argument("-n","--nodelist",help="file with list of swift nodes",
        type=str)
    parser.add_argument("-o","--object",help="name of test object",
        type=str,default='swiftperf')
    parser.add_argument("-s","--size",help="size of test object",
        type=int,default=1048576)
    parser.add_argument("-d","--delay",help="delay between runs in seconds",
        type=int,default=1)
    parser.add_argument("-i","--iterations",help="iterations (-1 infinite)",
        type=int,default=-1)

    return parser.parse_args()

def main():
    run_tests(parse_arguments())

if __name__ == '__main__':
    main()
