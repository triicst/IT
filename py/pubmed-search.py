#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv, json, requests, os
from Bio import Entrez
from collections import OrderedDict

ambig_lastnames = ['anderson', 'baker', 'chen', 'cooper', 'dai', 'di', 'fang',
'flowers', 'green', 'hansen', 'he', 'hsu', 'huang', 'jones', 'ko', 'lee', 'li',
'ma', 'martin', 'miller', 'nelson', 'olson', 'schwartz', 'smith', 'sun',
'thompson', 'wang', 'wu', 'zhao', 'zheng']

def main():

    author = args.author

    j = getToolbox('https://toolbox.fhcrc.org/json/faculty.json')

    if not os.path.exists(author):

        if "_" in author:
            author=author.replace('_', ' ')
        lastname, forename, initial, initials = splitName(author)
        initial_or_forename = initial
        if lastname.lower() in ambig_lastnames:
            initial_or_forename = forename

        papers = getPapers("%s %s" % (lastname, initial_or_forename))
        pubrows=showPapers(j, papers, author, lastname, forename, initials)
        #print(lastname, forename, initials)

        return True

    #namein="/home/petersen/test/GizmoUsageScientificPrioritiesShort.csv"
    #nameout="/home/petersen/test/GizmoUsagePublicationsShort.csv"

    namein=author
    nameout=os.path.splitext(namein)[0]+'-publications.csv'

    with open(namein, 'r') as infile, open(nameout, 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        writer.writerow(['PI','author','article_id', 'title', 'year', 'month',
                 'num_authors', 'rank', 'num_peers', 'peers', 'journal', 'ISSN'])
        for row in csv.reader(infile):

            if not '_' in row[0]:
                continue

            displayName = jsearchone(j,"pi_dept", row[0], "displayName")
            if displayName:
                lastname, forename, initial, initials = splitName(displayName)
            else:
                author = row[0].replace('_', ' ')
                lastname, forename, initial, initials = splitName(author)

            initial_or_forename = initial
            if lastname.lower() in ambig_lastnames:
                initial_or_forename = forename
            print('### Search Author :', "%s %s" % (lastname, initial_or_forename))
            papers = getPapers("%s %s" % (lastname, initial_or_forename))
            pubrows = showPapers(j, papers, row[0], lastname, forename, initial)

            for pubrow in pubrows:
                #print (pubrow)
                writer.writerow(pubrow)

def showPapers(j, papers, pi, lastname, forename, initial):
    if not papers:
        return []
    k=0
    rank=0
    month=''
    year=''
    aid=''
    ISSN=''
    rows=[]
    for i, paper in enumerate(papers['PubmedArticle']):
        article = paper['MedlineCitation']['Article']
        journal = article['Journal']
        authors = article['AuthorList']
        aids=article['ELocationID']
        journalinfo = paper['MedlineCitation']['MedlineJournalInfo']

        retlst = []
        if len(authors) > 0:
            rank, author = authorRank(authors, lastname, forename, initial)

        #if rank == 0 or (rank > 1 and rank < len(authors)-3):
            #only show pubs with first and last author
        #    continue
        #if len(aids)==0:
        #    continue
        if 'Month' in journal['JournalIssue']['PubDate']:
            month=journal['JournalIssue']['PubDate']['Month']
            year=journal['JournalIssue']['PubDate']['Year']

        if year == '' or year < args.sinceyear:
            continue

        k+=1
        print("%d) %s" % (k, article['ArticleTitle']))

        if 'ISSNLinking' in journalinfo:
            ISSN = journalinfo['ISSNLinking']
        if len(aids)>0:
            aid=aids[0]
            print("    ID: %s" % aids[0])

        print("    Journal: %s, ISSN: %s" % (journal['Title'], ISSN))

        print("    Year: %s, Month: %s" % (year, month))

        #print(json.dumps(article, indent=2))
        #sys.exit()

        print("    # of Authors: ", len(authors))
        print("    %s rank: %s" % (author, rank) )

        peers = getPeers (j, authors, lastname, forename, initial)
        if peers:
            print('    PEERS ***:', ', '.join(peers))

        #if 'GrantList' in article:
            #ret = getgrants(article['GrantList'])

        # returns pi, author, aid, title, year, month, authorcount, authorpos, journal, issn

        rows.append([pi, author, aid,
              article['ArticleTitle'].encode('ascii','ignore').decode(),
              year, month, len(authors), rank, len(peers), ';'.join(peers),
              journal['Title'], ISSN])

    return rows

def getgrants (grants):
    for g in grants:
        if 'GrantID' in g:
            print("   ",g['GrantID'],"(",g['Agency'],")")

def authorRank (authors, lastname, forename, initials):
    """ get the position of a person in an author list, first do first name
        matching, then in a second loop try matching of initials.
    """
    i=0
    retlist=[]
    for a in authors:
        i+=1
        #if a['AffiliationInfo']:
        #    print ("Affiliation: ", a['AffiliationInfo'][0]['Affiliation'])
        if 'LastName' in a and lastname:
            if 'ForeName' in a:
                #print ("FORENAME", a['ForeName'], forename)
                if a['LastName'].lower() == lastname.lower() and \
                        (forename.lower() in a['ForeName'].lower() \
                        or a['ForeName'].lower() in forename.lower()):
                    #retlist = [i, a['LastName'] + ' ' + a['ForeName'] + ' (' + a['Initials'] + ')']
                    retlist = [i, a['LastName'] + ' ' + a['ForeName']]


    if len(retlist) > 0:
        return retlist
    i=0
    for a in authors:
        i+=1
        if 'LastName' in a:
            if 'Initials' in a:
                #print("LAST", a['LastName'], lastname)
                if a['LastName'].lower() == lastname.lower() and initials.lower() \
                                      in a['Initials'].lower():
                    retlist = [i, a['LastName'] + ' ' + a['Initials']]

    if len(retlist) > 0:
        return retlist
    else:
        return 0, ""

def getPeers (j, authors, lastname, forename, initial):
    """ get peer faculty from same institution, affiliation info in pub needs
        to include string 'Fred Hutch'
    """
    peers=[]
    if not j:
        return peers
    HutchPIs=uniq(jget(j,'displayName'))
    for a in authors:
        if not 'LastName' in a: continue
        if not 'ForeName' in a: continue
        if not 'Initials' in a: continue
        if not 'AffiliationInfo'  in a: continue
        affinfo = a['AffiliationInfo']
        aff = ''
        if len(affinfo) > 0:
            aff = affinfo[0]['Affiliation']
        if not 'Fred Hutch' in aff:
            continue
        for hutchpi in HutchPIs:
            hlast, hfore, hinitial, hinitials = splitName(hutchpi)
            # skip current author
            if hlast.lower() == lastname.lower():
                #print ("***hlast, hfore, hinit:", hlast, hfore, hinit)
                #print ("***lastname, forename, initials:", lastname, forename, initials)
                if (hfore.lower() in forename.lower() or \
                         forename.lower() in hfore.lower()): continue
                if hinitial.lower() == initial.lower(): continue

            if a['LastName'].lower() == hlast.lower():
                if a['Initials'][0].lower() == hinitial.lower():
                    peers.append(hlast + ' ' + hfore)
    return peers

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

def getPapers(author):
    query = "Fred Hutch*[Affiliation] AND %s[Author]" % author
    results = search(query)
    id_list = results['IdList']
    papers = fetch_details(id_list)
    if not papers:
        print("no papers found for %s" % author)
        return []
    return papers

def search(query):
    Entrez.email = 'your.email@example.com'
    handle = Entrez.esearch(db='pubmed',
                            sort='relevance',
                            retmax='2000',
                            retmode='xml',
                            term=query)
    results = Entrez.read(handle)
    return results

def fetch_details(id_list):
    ids = ','.join(id_list)
    try:
        Entrez.email = 'your.email@example.com'
        handle = Entrez.efetch(db='pubmed',
                               retmode='xml',
                               id=ids)
        results = Entrez.read(handle)
        return results
    except:
        return []

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
    parser = argparse.ArgumentParser(prog='pubmed-search',
        description='a tool for quickly searching ' + \
        'pubmed publications per Hutch author')
    parser.add_argument('author', action='store', default='',
        help='Please enter search as "Doe J" or "Doe John" ' + \
         'or enter a text file name (e.g. csv) that contains a list of authors!')
    parser.add_argument('--sinceyear', '-s', dest='sinceyear',
        action='store', default='',
        help=' search for authorship since year ' + \
         '!')
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
