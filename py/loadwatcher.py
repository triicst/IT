#! /usr/bin/env python3

# loadwatcher checks cpu util per user on a linux machine and
# send warning messages to users who pass a certain threshold 
#
# loadwatcher dirkpetersen / Oct 2017
#

import sys, os, argparse, psutil, time, socket, tempfile, datetime, re, glob

# all processes that use minpercent cpu are aggregated to calculate maxpercent 
minpercent=40
# send a warning email to users with cpu util > maxpercent
maxpercent=400
# kill all processes of a user with cpu util >  killpercent
killpercent=1600

class KeyboardInterruptError(Exception): pass

def main():

    # Set up logging.  Show error messages by default, show debugging 
    # info if specified.
    log = logger('loadwatcher', args.debug)
    log.debug('loadwatcher - starting execution at %s' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.debug('Parsed arguments: %s' % args)

    # initialize cpu_percent calculator 
    [(p.pid, p.info['cpu_percent']) for p in psutil.process_iter(attrs=[ 'cpu_percent'])]
    time.sleep(1)

    userutil={}
    for p in psutil.process_iter(attrs=['name', 'username', 'cpu_percent']):
        if p.info['username'] != 'root' and p.info['cpu_percent'] > minpercent:
            if p.info['username'] in userutil:
                userutil[p.info['username']]+=p.info['cpu_percent']
            else:
                userutil[p.info['username']]=p.info['cpu_percent']
                
    # if user is idle, delete stub /tmp/loadwatcher.py_USER.stub
    for fl in glob.glob(tempfile.gettempdir()+'/'+os.path.basename(__file__)+'_*.stub'):
        if not fl[20:-5] in userutil:
            log.info('deleting stub %s ...' % fl)
            os.unlink(fl)
                
    hostname = socket.gethostname()
    
    for user, percent in userutil.items():
        log.debug('user:%s, percent:%s' % (user, percent))
        # see if we need to kill anything 
        if percent>killpercent:
            try:
                if user != '':
                    os.spawnlp(os.P_NOWAIT, 'killall', '-9', '-v', '-g', '-u', user)
                    log.info('executed killall -9 -v -g -u %s' % user)
                    to=user
                    if args.onlybcc and args.bcc != '':
                        to=args.bcc
                    send_mail([to,], "%s: Your jobs have been removed!" % (hostname.upper()),
                        "%s, your CPU utilization on %s is currently %s %%!\n\n" \
                        "For short term jobs you can use no more than %s %%\n" \
                        "or %s CPU cores on the Rhino machines.\n" \
                        "We have removed all your processes from this computer.\n" \
                        "Please try again and submit batch jobs\n" \
                        "or use the 'grabnode' command for interactive jobs.\n\n" \
                        "see http://scicomp.fhcrc.org/Gizmo%%20Cluster%%20Quickstart.aspx\n" \
                        "or http://scicomp.fhcrc.org/Grab%%20Commands.aspx\n" \
                        "or http://scicomp.fhcrc.org/SciComp%%20Office%%20Hours.aspx\n" \
                        "\n" % (user, hostname, int(percent), maxpercent, maxpercent/100), bcc=[args.bcc,])                    
                    log.info('Sent kill notification email to %s' % user)
                else:
                    log.warning('Nobody to send emails to')
            except:
                e=sys.exc_info()[0]
                sys.stderr.write("Error in send_mail while sending to '%s': %s\n" % (user, e))
                log.error("Error in send_mail while sending to '%s': %s\n" % (user, e))
                if args.erroremail:
                    send_mail([args.erroremail,], "Error - loadwatcher",
                        "Please debug email notification to user '%s', Error: %s\n" % (user, e))
                else:
                    sys.stderr.write('no option --error-email given, cannot send error status via email\n')
                    log.error('no option --error-email given, cannot send error status via email\n')         
            
            continue
        
        # see if we need to send a warning 
        stub = os.path.join(tempfile.gettempdir(),os.path.basename(__file__)+'_'+user+'.stub')                                
        if percent>maxpercent:            
            if os.path.exists(stub):
                log.info('stub %s already exists, not sending email' % stub) 
                continue
            try:
                if user != '':
                    to=user
                    if args.onlybcc and args.bcc != '':
                        to=args.bcc
                    send_mail([to,], "%s: You are using too many CPU cores!" % (hostname.upper()),
                        "%s, your CPU utilization on %s is currently %s %%!\n\n" \
                        "For short term jobs you can use no more than %s %%\n" \
                        "or %s CPU cores on the Rhino machines.\n" \
                        "Please reduce your load now and submit batch jobs\n" \
                        "or use the 'grabnode' command for interactive jobs.\n\n" \
                        "see http://scicomp.fhcrc.org/Gizmo%%20Cluster%%20Quickstart.aspx\n" \
                        "or http://scicomp.fhcrc.org/Grab%%20Commands.aspx\n" \
                        "or http://scicomp.fhcrc.org/SciComp%%20Office%%20Hours.aspx\n" \
                        "\n" % (user, hostname, int(percent), maxpercent, maxpercent/100), bcc=[args.bcc,])
                    os.mknod(stub)                    
                    log.info('Sent warning email to %s' % user)  
                else:
                    log.warning('Nobody to send emails to')
            except:
                e=sys.exc_info()[0]
                sys.stderr.write("Error in send_mail while sending to '%s': %s\n" % (user, e))
                log.error("Error in send_mail while sending to '%s': %s\n" % (user, e))
                if args.erroremail:
                    send_mail([args.erroremail,], "Error - loadwatcher",
                        "Please debug email notification to user '%s', Error: %s\n" % (user, e))
                else:
                    sys.stderr.write('no option --error-email given, cannot send error status via email\n')
                    log.error('no option --error-email given, cannot send error status via email\n') 

            
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
    parser = argparse.ArgumentParser(prog='loadwatcher',
        description='hecks cpu util per user on a linux machine and ' + \
        'send warning messages to users who pass a certain threshold')
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true',
        help='verbose output for all commands',
        default=False )
    parser.add_argument( '--only-bcc', '-s', dest='onlybcc', action='store_true',
        help='do not send any emails to end users, only to the bcc email',
        default=False )
    parser.add_argument( '--bcc', '-c', dest='bcc',
        action='store',
        help='email address to be blind carbon copied.',
        default='' )        
    parser.add_argument( '--error-email', '-e', dest='erroremail',
        action='store',
        help='send errors to this email address.',
        default='' )        
    args = parser.parse_args()        
    if args.debug:
        print('DEBUG: Arguments/Options: %s' % args)    
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())
