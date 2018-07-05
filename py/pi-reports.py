#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv, json, requests
from collections import OrderedDict

def main():

    p = getToolbox('https://toolbox.fhcrc.org/json/pi_all.json')
    u = getToolbox('https://toolbox.fhcrc.org/json/staff_all.json')

    empIDs = jget(u, 'employeeID')
    mgrIDs = jget(u, 'mgrID')
    PI_IDs = jget(p, 'employeeID')
    #pi_depts = jget(p, 'pi_dept')
#    print(PI_IDs)

    staff_in_reporting_line = {} #OrderedDict()

    for empid in uniq(empIDs):
        paygroup = jsearchone(u,'employeeID',empid,'paygroup')
        if paygroup != 'FHC':
            continue
        division = jsearchone(u,'employeeID',empid,'division')
        if division in ['AD', 'HD', 'SR']:
            continue
        uid = jsearchone(u,'employeeID',empid,'uid')
        #if uid == 'rbradley': 
        #     print("begin", uid)
        if not uid:
            #print ('          NOOOOOOO uid')
            continue 
        #if uid in ['cmoravec', 'mwilson', 'lgetzend']:
        #    continue
        pi_id = getPI(u, empid, PI_IDs)
        if not pi_id:
            #print ('         NOOOOOOOOO pi_id')
            continue
        pi = jsearchone(p,'employeeID',pi_id,'pi_dept')
        #if uid == 'rbradley':
        #     print('PI', pi) 
        if not pi:
            #print('        nooooooo PI',pi)
            continue
        if pi in staff_in_reporting_line:
            #print ('staaaff', staff_in_reporting_line[pi])
            users = staff_in_reporting_line[pi]
            users.append(uid)
            staff_in_reporting_line[pi] = users
        else:
            #print('first', pi, uid)
            users = []
            users.append(uid)
            staff_in_reporting_line[pi] = users
            #print ("FIRST STAFF", staff_in_reporting_line[pi])
    
    
    #print(staff_in_reporting_line['stanford_j'])

    # If PI has more than 15 reports remove people from other departments 
    for k, v in staff_in_reporting_line.items():
        if len(v) > 10:
            remainder = []
            for uid in v:
                #print(k, jsearchone(p,'pi_dept',k,'department'))
                #print(uid, jsearchone(u,'uid',uid,'department'))

                if jsearchone(u,'uid',uid,'department') == jsearchone(p,'pi_dept',k,'department'):
                    #print("same department", uid, pi_id)
                    remainder.append(uid)
            
            if len(remainder) > 0:
                staff_in_reporting_line[k] = remainder

    with open('c:/temp/test/moin.txt', 'w') as outfile:
        outfile.write('PI\tlevel\tusers\tuserlist\n')
        for k, v in staff_in_reporting_line.items():
            outfile.write('%s\t%s\t%s\t%s\n' % (k,getSeniority(p,k),len(v), v))
        #print (k,'|',len(v),'|', v)


def getSeniority(p, pi_dept):
    # returns 3 for Full Member, 2 for Associate Member and 1 for Assistant 
    job = jsearchone(p,'pi_dept',pi_dept,'jobTitle')
    seniority = 3
    if job == "Assistant Member":
        seniority = 1
    elif job == "Associate Member":
        seniority = 2
    return seniority

def getPI(u, empid, PI_IDs):
    # returns the empID of the next PI up the reporting chain #
    while True:
        if empid in PI_IDs:
            return empid # user is a PI
        mgrids = jsearchall(u,'employeeID',empid,'mgrID')
        if len(mgrids) == 0:
            return None    
        for mgrid in mgrids:
            if mgrid in PI_IDs:
                return mgrid
        else:
            empid = mgrid
        

    #namein="/home/petersen/test/GizmoUsageScientificPrioritiesShort.csv"
    #nameout="/home/petersen/test/GizmoUsagePublicationsShort.csv"

    # namein=author
    # nameout=os.path.splitext(namein)[0]+'-publications.csv'

    # with open(namein, 'r') as infile, open(nameout, 'w') as outfile:
    #     writer = csv.writer(outfile, lineterminator='\n')
    #     writer.writerow(['PI','author','article_id', 'title', 'year', 'month',
    #              'num_authors', 'rank', 'num_peers', 'peers', 'journal', 'ISSN'])
    #     for row in csv.reader(infile):

    #         if not '_' in row[0]:
    #             continue

    #         displayName = jsearchone(j,"pi_dept", row[0], "displayName")
    #         if displayName:
    #             lastname, forename, initial, initials = splitName(displayName)
    #         else:
    #             author = row[0].replace('_', ' ')
    #             lastname, forename, initial, initials = splitName(author)

    #         initial_or_forename = initial
    #         if lastname.lower() in ambig_lastnames:
    #             initial_or_forename = forename
    #         print('### Search Author :', "%s %s" % (lastname, initial_or_forename))
    #         papers = getPapers("%s %s" % (lastname, initial_or_forename))
    #         pubrows = showPapers(j, papers, row[0], lastname, forename, initial)

    #         for pubrow in pubrows:
    #             #print (pubrow)
    #             writer.writerow(pubrow)


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

def jsearchall(json,sfld,search,rfld):
    """ return the first search result of a column based search """
    lst = []
    for j in json:
        if j[sfld]==search:
            lst.append(j[rfld].strip())
    return lst

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



    #pgpass = os.getenv('PGPASSFILE', os.path.expanduser('~/.pgpass'))
    #if not os.path.exists(pgpass):
        #print('You need to create file ~/.pgpass that contains at least one line:')
        #print('hostname:port:database:username:password')
        #print('and has restricted permissions: chmod 600 ~/.pgpass')
        #print('Also please check https://www.postgresql.org/docs/current/static/libpq-pgpass.html')
        #return False

    ##args.dsn == 'postgresql://dirk@mydb:32063/petersen'
    ##args.csvfile = '/home/petersen/sc/data/slurm_jobs.csv'

    #if not args.dsn.startswith('postgresql://'):
        #dl = args.dsn.split(':')
        #args.dsn = 'postgresql://%s@%s:%s/%s' % (dl[3], dl[0], dl[1], dl[2])

    #try:
        #conn = psycopg2.connect(args.dsn)
        #cur = conn.cursor()
    #except (Exception, psycopg2.DatabaseError) as error:
        #print('Database error:', error)
        #return False

    #with open(args.csvfile, 'rb') as fh:
        #table_set = CSVTableSet(fh)
        #row_set = table_set.tables[0]
        ##print row_set.sample.next()
        #offset, headers = headers_guess(row_set.sample)
        #row_set.register_processor(headers_processor(headers))
        #row_set.register_processor(offset_processor(offset + rowtocheck))
        #types = type_guess(row_set.sample, strict=True)

    #myd = dict (zip (headers, types))
    #print("\nDetected columns & types:\n", myd, '\n')

    #table = os.path.splitext(os.path.basename(args.csvfile))[0]
    #table = table.replace('-','_')
    #table = table.replace(' ','_')
    #create_sql = "CREATE TABLE %s (" % table
    #idh = 0
    #for h in headers:
        #myt = "TEXT"
        #if str(types[idh]) == 'Integer':
            #myt = 'BIGINT'
        #elif str(types[idh]) == 'Bool':
             #myt = 'BIGINT'
        #elif str(types[idh]) == 'Decimal':
             #myt = 'DECIMAL'

        #create_sql += "%s %s, " % (h,myt)
        #idh += 1
    #create_sql = create_sql[:-2] + ');'

    #print("\ncreating postgres table '%s':\n" % table, create_sql, '\n')
    #try:
        #if args.overwrite:
            #drop_sql = 'DROP TABLE IF EXISTS %s' % table
            #cur.execute(drop_sql)
            #conn.commit()
        #cur.execute(create_sql)
        #conn.commit()
    #except (Exception, psycopg2.DatabaseError) as error:
        #print('Database error:', error)
        #sys.exit()

    #print("\nloading data .... ")

    #with open(args.csvfile, 'rb') as fh:
        #sample_text = ''.join(str(fh.readline()) for x in range(3))
        #try:
            #dialect = csv.Sniffer().sniff(sample_text)
            #if dialect.delimiter == 't':
                #delim = '\t'
            #else:
                #delim = dialect.delimiter
        #except:
            #delim = ","
        #copy_sql = "COPY %s FROM stdin WITH CSV HEADER DELIMITER as '%s'" % \
                   #(table, delim)
        #try:
            #cur.copy_expert(sql=copy_sql, file=fh)
            #conn.commit()
            #cur.close()
        #except (Exception, psycopg2.DatabaseError) as error:
            #print('Database error:', error)

    #print('Done !')


def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='faculty-reports',
        description='a tool for quickly searching ' + \
        'pubmed publications per Hutch author')
    #parser.add_argument('author', action='store', default='',
    #    help='Please enter search as "Doe J" or "Doe John" ' + \
    #     'or enter a text file name (e.g. csv) that contains a list of authors!')
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
