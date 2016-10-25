#!/usr/bin/env python3

import argparse
import csv
import pwd

import sys,os
import getpass

import multiprocessing

import logging
import logging.handlers

import lflib

owner_files_dict={}

# initialize logging to syslog - borrowed from leftover
def init_logging():
    crier=logging.getLogger('crybaby')
    crier.setLevel(logging.DEBUG)
    syslog=logging.handlers.SysLogHandler(
        address='/dev/log',
        facility='daemon'
    )
    crier.addHandler(syslog)

    crier.info('lf-backup starting')
    crier.debug('DEBUG: lf-backup syslog logging setup complete')

    return crier

# read csv file into list using field to pick, default to final field
def read_csv(csv_file,field=-1):
    csv_items=[]

    #crier.info("lf-backup: backing up from csv %s" % (csv_file))

    try:
        with open(csv_file) as f:
            for row in csv.reader(f):
                if field==-1 or (field>=0 and field<len(row)):
                    csv_items.append(row[field])
    except OSError:
        print("Error: missing CSV file",csv_file)
        #crier.info("lf-backup: failed to find csv %s" % (csv_file))

    return csv_items

# return true if object exists and size/mtime identical
# mtime comparison currently disabled due to format mismatch
def check_stored_object(name,container,container_dir,size,mtime):
    if name in container_dir:
       #if container_dir[name][0]==size and container_dir[name][1]==mtime:
       if container_dir[name][0]==size:
          return True

    return False

def generate_destname(prefix,filename):
    if prefix and filename.startswith(prefix):
       destname=filename[len(prefix):]
    else:
       destname=filename

    # elide leading / from destname
    if destname[0]=='/':
        destname=destname[1:]

    return destname

# file to backup, syslog object
def backup_file(filename,container,prefix,container_dir,crier):
    global owner_files_dict

    #print("considering file",filename)

    destname=generate_destname(prefix,filename)

    #print("container",container,"dest",destname)

    try:
        statinfo=os.stat(filename)
    except OSError:
        print("Error: missing file",filename)
        #crier.info("lf-backup: failed to find %s" % (filename))
        return

    if check_stored_object(destname,container,container_dir,statinfo.st_size,
        statinfo.st_mtime):
        print("file",filename,"is already current")
        #crier.info("lf-backup: %s is already current" % (filename))
    else:
        # append file to dict keyed to uid for later mailed report
        if statinfo.st_uid not in owner_files_dict:
            owner_files_dict[statinfo.st_uid]=[]
        owner_files_dict[statinfo.st_uid].append(filename)

        # upload file to swift to container:destname
        print("uploading file",filename)
        #crier.info("lf-backup: uploading file %s" % (filename))
        lflib.upload_to_swift(filename,destname,container)

# build db of container files by name
def build_container_dir(container):
    container_dir={}

    c_objs=lflib.get_sw_container(container)
    for obj in c_objs:
        container_dir[obj['name']]=[obj['bytes'],obj['last_modified']] 

    return container_dir

# shell to call backup_file with correct separate parameters
# each parameter is [filename,parse_args,container_dir,crier]
def backup_file_mp(x):
    backup_file(x[0],x[1].container,x[1].prefix,x[2],x[3])

# args from argparse, syslog object
def backup(parse_args,crier):
    input=[]

    if parse_args.csv:
        input=read_csv(parse_args.input)
    elif parse_args.sql:
        print("Error: SQL table read not yet implemented")
    else:
        print("Fatal error: no legal input type specified!")

    container_dir=build_container_dir(parse_args.container)

    # build parallel parameter list
    segments=[[e,parse_args,container_dir,crier] for e in input]

    p=multiprocessing.Pool(parse_args.parallel)
    p.map(backup_file_mp,segments)

# send SMTP mail to username containing filelist
def mail_report(username,files):
    print("mailing report to",username)

    # pretty print python list to text list
    body=""
    for file in files:
       body+=(file+"\n")

    lflib.send_mail([username],"lf-backup: files uploaded",body)

# convert owner_files_dict into files by username and mail each
def mail_reports():
    global owner_files_dict

    for uid,files in owner_files_dict.items():
        mail_report(pwd.getpwuid(uid).pw_name,files)

# argparse config garbage
def parse_arguments():
    parser=argparse.ArgumentParser(
        description="Backup files to Swift from CSV or SQL")
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c","--csv",help="input from CSV file",
        action="store_true")
    group.add_argument("-s","--sql",help="input from SQL table",
        action="store_true")
    parser.add_argument('input',type=str)
    parser.add_argument("-p","--prefix",help="strip from source filename",
        type=str)
    parser.add_argument("-C","--container",help="destination container",
        type=str,required=True)
    parser.add_argument("-P","--parallel",help="number of parallel workers",
        type=int,default=5)

    return parser.parse_args()

def main():
    crier=init_logging()

    backup(parse_arguments(),crier)

    mail_reports()

if __name__ == '__main__':
    main()
