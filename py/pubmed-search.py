#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv, json
from Bio import Entrez
from collections import OrderedDict
  
def main():

    author = args.author
        
    results = searchHutchAuthor(author)
    id_list = results['IdList']
    papers = fetch_details(id_list)
    for i, paper in enumerate(papers['PubmedArticle']):
        article = paper['MedlineCitation']['Article']
        print("%d) %s" % (i+1, article['ArticleTitle']))        
        journal = article['Journal']
        authors = article['AuthorList']
        journalinfo = paper['MedlineCitation']['MedlineJournalInfo']
        
        ISSN = ''
        if 'ISSNLinking' in journalinfo:
            ISSN = journalinfo['ISSNLinking']
        
        print("    Journal: %s, ISSN: %s" % (journal['Title'], ISSN))
        if 'Month' in journal['JournalIssue']['PubDate']:
            print("    Year: %s, Month: %s" % (journal['JournalIssue']['PubDate']['Year'], 
                   journal['JournalIssue']['PubDate']['Month']))
            
        #print(json.dumps(article, indent=2))
        
        print("    # of Authors: ", len(authors))                
        ret = authorRank(authors, author)
        
        if 'GrantList' in article:
            ret = getgrants(article['GrantList'])
                
        
def getgrants (grants):
    for g in grants:
        if 'GrantID' in g:
            print("    ",g['GrantID'],"(",g['Agency'],")")
        
    
def authorRank (authors, author):
    lastname = ''
    forename = ''
    initials = ''
    if author[-2:-1] == ' ':
        lastname = author[:-2]
        initials = author[-1:]
    else:
        pos = author.find(' ')
        if pos > 0:
            lastname, forename = author.split(' ')
        else:
            lastname = author
            
    i=0
    for a in authors:
        i+=1
        #if a['AffiliationInfo']:
        #    print ("  ", a['AffiliationInfo'][0]['Affiliation'])            
        if 'LastName' in a:
            if a['LastName'] == lastname and a['ForeName'] == forename:
                print ("    ",i, a['LastName'], a['ForeName'])
            elif a['LastName'] == lastname and initials in a['Initials']:
                print ("    ",i, a['LastName'], a['Initials'])
    
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
    Entrez.email = 'your.email@example.com'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results


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
    parser = argparse.ArgumentParser(prog='pubmed',
        description='a tool for quickly searching ' + \
        'pubmed publications per hutch author')
    parser.add_argument('author', action='store', 
        help='Please enter search as "Doe J" or "Doe John" ' + \
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
