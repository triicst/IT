#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv, json, requests, os
from Bio import Entrez
from collections import OrderedDict
  
def main():

    author = args.author
    
    if not os.path.exists(author):
        
        if "_" in author:
            author=author.replace('_', ' ')
        lastname, forename, initials = splitName(author)
        results = searchHutchAuthor(lastname + ' ' + forename)            
        id_list = results['IdList']
        papers = fetch_details(id_list)
        if not papers:
            print("no papers found for %s" % author)
            return False
        
        pubrows=showPapers(papers, author, lastname, forename, initials)            
            
        return True
        
    #namein="/home/petersen/test/GizmoUsageScientificPrioritiesShort.csv"
    #nameout="/home/petersen/test/GizmoUsagePublicationsShort.csv"
    namein=author
    nameout=os.path.splitext(namein)[0]+'-publications.csv'
    
    j = requests.get('https://toolbox.fhcrc.org/json/pi_all.json').json()
    
    with open(namein, 'r') as infile, open(nameout, 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        for row in csv.reader(infile):
            
            if not '_' in row[0]:
                continue
            
            lastname = jsearchone(j,"pi_dept", row[0], "sn")    
            forename = jsearchone(j,"pi_dept", row[0], "givenName")
            
            author = row[0].replace('_', ' ')
                
            results = searchHutchAuthor(author)            
            id_list = results['IdList']
            papers = fetch_details(id_list)
            if not papers:
                print("no papers found for %s" % author)
                continue 
            
            if lastname:
                pubrows=showPapers(papers, row[0], lastname, forename)
            
                for pubrow in pubrows:
                    writer.writerow(pubrow)


def splitName(fullname):
        fullname = fullname.replace(',', ' ')
        fullname = fullname.replace('.', '')
        name=fullname.split()
        lastname = name[0]
        forename = ''
        initials = ''
        if len(name) > 1:
            forename=name[1]
            initials=forename[0]
            if len(name) == 3:
                forename = name[1] + ' ' + name[2]
                initials = name[1][0] + name[2][0]
        return lastname, forename, initials

def showPapers(papers, pi, lastname, forename, initials):
    j=0
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
            rank, author = authorRank(authors, lastname, forename, initials)
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
        
        j+=1
        print("%d) %s" % (j, article['ArticleTitle']))    
        
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
        
        
        if 'GrantList' in article:
            ret = getgrants(article['GrantList'])
        
        # returns pi, author, aid, title, year, month, authorcount, authorpos, journal, issn
        
        rows.append([pi, author, aid, article['ArticleTitle'], year, month, len(authors), 
               rank, journal['Title'], ISSN])
    return rows

        
def getgrants (grants):
    for g in grants:
        if 'GrantID' in g:
            print("   ",g['GrantID'],"(",g['Agency'],")")
        
    
def authorRank (authors, lastname, forename, initials):
    """ get the position of a person in an author list  """
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
                if a['LastName'].lower() == lastname.lower() and initials in a['Initials']:
                    retlist = [i, a['LastName'] + ' ' + a['Initials']]            

    if len(retlist) > 0:
        return retlist
    else:
        return 0, ""

def getPeers (j, authors, lastname, forename, initials):
    
    fullPINames=uniq(jget(j,'displayName'))
    
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
                if a['LastName'].lower() == lastname.lower() and initials in a['Initials']:
                    retlist = [i, a['LastName'] + ' ' + a['Initials']]            

    if len(retlist) > 0:
        return retlist
    else:
        return 0, ""
    
                
def search(query):
    Entrez.email = 'your.email@example.com'
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax='2000',
                            retmode='xml', 
                            term=query)
    results = Entrez.read(handle)
    return results

def searchHutchAuthor(author):
    query = "Fred Hutch*[Affiliation] AND %s[Author]" % author
    #query = "%s[Author]" % author
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
        return None

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
