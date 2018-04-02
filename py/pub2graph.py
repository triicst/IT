#! /usr/bin/env python

import os, sys, subprocess, argparse, csv, json, requests, os
from collections import OrderedDict

def main():
    if not os.path.exists(args.csvfile):
        print('file %s does not exist.' % args.csvfile)
        return False

    j = getToolbox('https://toolbox.fhcrc.org/json/faculty.json')

    namein=args.csvfile
    nameout=os.path.splitext(namein)[0]+'.dv'
    nameoutpdf=os.path.splitext(namein)[0]+'.pdf'

    pairs={}

    with open(namein, 'r') as infile, open(nameout, 'w') as outfile:
        outfile.write('graph {\n')
        for row in csv.reader(infile):

            if not '_' in row[0] or row[0] == 'PI':
                continue

            displayName1 = jsearchone(j,"pi_dept", row[0], "displayName")
            if not displayName1:
                print('displayName for %s not found' % row[0])
                continue
            division1=jsearchone(j,"pi_dept", row[0], "division")
            if division1 == "CB":
                division1 = "HB"
            
            #if division1 != 'VI':
            #    continue 
            department1=jsearchone(j,"pi_dept", row[0], "department")

            if row[9]:
                peers=getDisplayNames(j,row[9])
                for peer in peers:
                    displayName2 = peer
                    division2=jsearchone(j,"displayName", displayName2, "division")
                    if division2 == "CB":
                        division2 = "HB"                    
                    department2=jsearchone(j,"displayName", displayName2, "department")

                    if division1 != division2:
                        color ='red'
                    elif department1 != department2:
                        color = 'blue'
                    else:
                        color = 'black'

                    if displayName1 > displayName2:
                        pair='"%s (%s)" -- "%s (%s)"[color=%s' % (displayName1, 
                            division1, displayName2, division2, color)
                    else:
                        pair='"%s (%s)" -- "%s (%s)"[color=%s' % (displayName2, 
                            division2, displayName1, division1, color)

                    if pair in pairs:
                        pairs[pair] += 1
                        if pairs[pair] > 10:
                            pairs[pair] = 10
                    else:
                        pairs[pair] = 1

        for pair, width in pairs.items():
            # width needs to be devided by two, because the same pub has at least 2 collabs
            outfile.write('%s,penwidth=%s];\n' % (pair, width))  
        outfile.write('}\n')

        # unflatten -f -l 4 -c 6 input.dot | dot | gvpack -array_t6 | neato -s -n2 -Tpng -o output.png
        ret = subprocess.Popen("unflatten -f -l12 -c12 %s | dot -T pdf -o %s"
            % (nameout, nameoutpdf), shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)


def getDisplayNames(j, authors):
    #names=authors.split(';')
    names=[x.strip() for x in authors.split(';')]
    displayNames = []
    for name in names:
        lastname, forename, initial, initials = splitName(name)
        pi = "%s_%s" % (lastname.lower(), initial.lower())
        d = jsearchone(j,"pi_dept", pi, "displayName")
        if d:
            displayNames.append(d)
        else:
            d = jsearchone(j,"sn", lastname, "displayName")
            if d:
                displayNames.append(d)
            else:
                print('could not find %s in the faculty database.' % name)
    return displayNames


def splitName(fullname):
    fullname = fullname.replace(',', ' ')
    fullname = fullname.replace('.', '')
    name=fullname.split()
    lastname = name[0]
    forename = ''
    initials = ''
    initial = ''
    if len(name) > 1:
        forename=name[1]
        initials=forename[0]
        initial=initials
        if len(name) == 3:
            forename = name[1]
            initials = name[1][0] + name[2][0]
            initial = name[1][0]
    #print ('** lastname, forename, initial, initials', lastname, forename, initial, initials)
    return lastname, forename, initial, initials


def getToolbox(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as err:
        print ("Error: {}".format(err))
        return ""


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
    parser = argparse.ArgumentParser(prog='pub2graph',
        description='tool for turning pub info into graph ' + \
        'pubmed publications per Hutch author')
    parser.add_argument('csvfile', action='store', default='',
        help='Please the filename of a csv file ' + \
         'that contains authorship information')
    #parser.add_argument('--sinceyear', '-s', dest='sinceyear',
    #    action='store', default='',
    #    help=' search for authorship since year ' + \
    #     '!')
    #parser.add_argument('dsn', action='store',
        #help='postgres connection string, format postgresql://username@hostname:port/database ' + \
         #'or ~/.pgpass style credentials such as hostname:port:database:username')
    #parser.add_argument('csvfile', action='store',
        #help='csv file you want to upload to postgres ' + \
            #'the delimiter can be a tab, pipe or a comma')
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
