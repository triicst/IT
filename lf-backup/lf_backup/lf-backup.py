#!/usr/bin/env python3

import argparse
import csv
import pwd

import sys,os

import logging
import logging.handlers

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
def check_stored_object(name,container,size,mtime):
    # while in development
    return False

# file to backup, syslog object
def backup_file(filename,container,prefix,crier):
    global owner_files_dict

    print("backing up file",filename)
    #crier.info("lf-backup: backing up file %s" % (filename))

    if prefix and filename.startswith(prefix):
       destname=filename[len(prefix):]
    else:
       destname=filename

    print("container",container,"dest",destname)

    try:
        statinfo=os.stat(filename)
    except OSError:
        print("Error: missing file",filename)
        #crier.info("lf-backup: failed to find %s" % (filename))
        return

    if check_stored_object(destname,container,statinfo.st_size,
        statinfo.st_mtime):
        print("file",filename,"is already current")
        #crier.info("lf-backup: %s is already current" % (filename))
    else:
        # append file to dict keyed to uid for later mailed report
        if statinfo.st_uid not in owner_files_dict:
            owner_files_dict[statinfo.st_uid]=[]
        owner_files_dict[statinfo.st_uid].append(filename)

    # upload file to swift to container:destname

# args from argparse, syslog object
def backup(parse_args,crier):
    if parse_args.csv:
        input=read_csv(parse_args.input)
    elif parse_args.sql:
        print("Error: SQL table read not yet implemented")
        sys.exit()
    else:
        print("Fatal error: no legal input type specified!")
        sys.exit()

    for file in input:
        backup_file(file,parse_args.container,parse_args.prefix,crier)

# send SMTP mail to username containing filelist
def mail_report(username,files):
    print("mailing report to",username,"listing",files)

# convert owner_files_dict into files by username and mail each
def mail_reports():
    global owner_files_dict

    for uid,files in owner_files_dict.items():
        mail_report(wd.getpwuid(uid).pw_name,files)

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

    return parser.parse_args()

def main():
    crier=init_logging()

    backup(parse_arguments(),crier)

    mail_reports()

if __name__ == '__main__':
    main()
