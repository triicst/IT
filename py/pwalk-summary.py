#! /usr/bin/env python3

# pwalk-summary summary aggregates pwalk output and groups by filetype or user 
#
# pwalk-summary dirkpetersen / Jul 2018
#

import sys, os, argparse, time, pandas, dask, dask.dataframe, glob
#import time, socket, subprocess, numpy, tempfile, datetime, re

class KeyboardInterruptError(Exception): pass

def main():

    if args.sfolder == args.dfolder:
        print('   --sfolder and --dfolder need to be different folders.')
        return False

    cols = ['inode', 'parentinode', 'directorydepth', 'filename', 'fileExtension', \
          'UID', 'GID', 'st_size', 'st_dev', 'st_blocks', 'st_nlink', 'st_mode', \
          'atime', 'mtime', 'ctime', 'count_files', 'sum_size']

    dtypes = {'inode':int, 'parentinode':int, 'directorydepth':int, \
          'filename':str, 'fileExtension':str, 'UID':int, 'GID':int, \
          'st_size':int, 'st_dev':int, 'st_blocks':int, 'st_nlink':int, \
          'st_mode':int, 'atime':int, 'mtime':int, 'ctime':int, \
          'count_files':int, 'sum_size':int}

    if args.usedask:
        print('\n   loading csv files from %s into dask ...' % args.sfolder)
        df = dask.dataframe.read_csv('%s/*.csv' % args.sfolder, header=None, names=cols, dtype=dtypes)
    else:
        print('\n   loading csv files from %s into pandas ...' % args.sfolder)
        df = pandas.concat([pandas.read_csv(f,header=None, names=cols, dtype=dtypes) 
            for f in glob.glob('%s/*.csv' % args.sfolder)], ignore_index=True)

    aggregations = {
        'st_size': ['sum', 'mean'],
        'fileExtension': 'count'
    }

    print('\n   grouping data by extension ...')
    ext = df.groupby(["fileExtension"]).agg(aggregations) 
    print('\n   grouping data by user ...')
    uid = df.groupby(["UID"]).agg(aggregations)

    print('\n   writing result csv files to %s ...' % args.dfolder)
    if args.usedask:
        ext.to_csv(os.path.join(args.dfolder,'dask-byextension.*.csv'), header=True)
        uid.to_csv(os.path.join(args.dfolder,'dask-byuser.*.csv'), header=True)    
    else:
        ext.to_csv(os.path.join(args.dfolder,'pandas-byextension.csv'), header=True)
        uid.to_csv(os.path.join(args.dfolder,'pandas-byuser.csv'), header=True)    

def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):

    if sys.version_info[0] == 2:
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEBase import MIMEBase
        from email.MIMEText import MIMEText
        from email.Utils import COMMASPACE, formatdate
        from email import Encoders
    else:
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.utils import COMMASPACE, formatdate
        from email import encoders as Encoders
    from string import Template
    import socket
    import smtplib

    if not isinstance(to,list):
        print("the 'to' parameter needs to be a list")
        return False    
    if len(to)==0:
        print("no 'to' email addresses")
        return False
    
    myhost=socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')
        
    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
           '.'.join(myhost.split(".")[-2:]) #extract domain from host
    tc=0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc]=t + '@' + '.'.join(myhost.split(".")[-2:])
        tc+=1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template('This is a notification message from $application, running on \n' + \
            'host $host. Please review the following message:\n\n' + \
            '$notify_text\n\nIf output is being captured, you may find additional\n' + \
            'information in your logs.\n'
            )
    host_name = socket.gethostname()
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        message.attach(part)

    addresses = []
    for x in to:
        addresses.append(x)
    for x in cc:
        addresses.append(x)
    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(smtphost)
    smtp.sendmail(fromaddr, addresses, message.as_string())
    smtp.close()

    return True

def get_mx_from_email_or_fqdn(addr):
    """retrieve the first mail exchanger dns name from an email address."""
    # Match the mail exchanger line in nslookup output.
    MX = re.compile(r'^.*\s+mail exchanger = (?P<priority>\d+) (?P<host>\S+)\s*$')
    # Find mail exchanger of this email address or the current host
    if '@' in addr:
        domain = addr.rsplit('@', 2)[1]
    else:
        domain = '.'.join(addr.rsplit('.')[-2:])
    p = os.popen('/usr/bin/nslookup -q=mx %s' % domain, 'r')
    mxes = list()
    for line in p:
        m = MX.match(line)
        if m is not None:
            mxes.append(m.group('host')[:-1])  #[:-1] just strips the ending dot
    if len(mxes) == 0:
        return ''
    else:
        return mxes[0]

def logger(name=None, stderr=False):
    import logging, logging.handlers
    # levels: CRITICAL:50,ERROR:40,WARNING:30,INFO:20,DEBUG:10,NOTSET:0
    if not name:
        name=__file__.split('/')[-1:][0]
    l=logging.getLogger(name)
    l.setLevel(logging.INFO)
    f=logging.Formatter('%(name)s: %(levelname)s:%(module)s.%(lineno)d: %(message)s')
    # logging to syslog
    s=logging.handlers.SysLogHandler('/dev/log')
    s.formatter = f
    l.addHandler(s)
    if stderr:
        l.setLevel(logging.DEBUG)
        # logging to stderr        
        c=logging.StreamHandler()
        c.formatter = f
        l.addHandler(c)
    return l

def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='slurm-limiter',
        description='slurm-limiter checks the current util of a slurm ' + \
        'cluster and adjusts the account and user limits dynamically within certain range')
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true',
        help='verbose output for all commands',
        default=False ) 
    parser.add_argument( '--error-email', '-e', dest='erroremail',
        action='store',
        help='send errors to this email address.',
        default='' )   
    parser.add_argument( '--sfolder', '-s', dest='sfolder',
        action='store',
        help='name of the source folder for input csv files (default: current folder)',
        default='.' )           
    parser.add_argument( '--dfolder', '-d', dest='dfolder',
        action='store',
        help='name of the destination folder for output csv files (default: current folder)',
        default='.' )  
    parser.add_argument( '--use-dask', '-u', dest='usedask',
        action='store_true',
        help='instead of pandas use the higher performance dask library (default: False)',
        default=False )  
        
    args = parser.parse_args()        
    if args.debug:
        print('DEBUG: Arguments/Options: %s' % args)    
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())
