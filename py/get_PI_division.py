#! /usr/bin/env python3

"""
insert
"""

import sys, os, argparse, json, requests, csv
tmpdir = '/var/tmp'

# the user database of potential scientific computing users
j = requests.get('https://toolbox.fhcrc.org/json/pi_all.json').json()

def main():

    # adding users #########################################

    #uids = uniq(jget(j, 'uid'))
    #uids_add, uids_del = listcompare('%s/pi_uids_last.json' % tmpdir, uids)

    prio = {}
    prio["CR"] = 'A'
    prio["PH"] = 'B'
    prio["VI"] = 'C'
    prio["BS"] = 'D'
    prio["CB"] = 'D'
    prio["AD"] = 'D'

    nameout="C:\\Users\\petersen\\Desktop\\SciComp\\GizmoUsageScientificPriorities1.csv"
    namein="C:\\Users\\petersen\\Desktop\\SciComp\\GizmoUsageScientificPriorities.csv"

    with open(namein, 'r') as infile, open(nameout, 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        for row in csv.reader(infile):
            div = jsearchone(j,"pi_dept", row[0], "division")
            #print(row[0], div)
            if div:
                print([row[0], div, prio[div], row[3]])
                writer.writerow([row[0], div, prio[div], row[3]])
            else:
                print(row)
                writer.writerow(row)


            #writer.writerow([timestamp] + row[1:])



########################################################################

# some helper functions

def jsearch(json,sfld,search,rfld):
    """ return a list of values from a column based on a search """
    lst=[]
    for j in json:
        if j[sfld]==search or search == '*':
            lst.append(j[rfld].strip())
    return lst

def jgetonerow(j,sfld,search):
    """ return a row based  on a search """

    for row in j:
        if row[sfld]==search or search == '*':
            return row

def jsearchone(json,sfld,search,rfld):
    """ return the first search result of a column based search """
    for j in json:
        if j[sfld]==search:
            return j[rfld].strip()

def jget(json,rfld):
    """ return all values in one column """
    lst=[]
    for j in json:
        if j[rfld].strip() != "":
            lst.append(j[rfld].strip())
    return lst

def uniq(seq):
    """ remove duplicates from a list """
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())



def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='xxxx',
        description='yyyyyyyyyyyyyyyyyyyy ' + \
            '(xxxx)')
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true', default=False,
        help="do not send an email but print the result to  console")
    #parser.add_argument('--mailto', '-m', dest='mailto', action='store', default='',
        #help='send email address to notify of a new deployment.')

    return parser.parse_args()

if __name__=="__main__":
    args = parse_arguments()
    try:
        main()
    except KeyboardInterrupt:
        print ('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
