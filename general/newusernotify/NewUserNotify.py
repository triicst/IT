#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#  send notifications to a helpdesk or onboarding process
#  when new users show up in active directory.
#  The script runs a configurator to setup custom filters
#  if it is invoked without command line options. 
#  It expects an active kerberos ticket cache but can be 
#  modfied to work with a service account
#  dirkpetersen 2016

import sys, os, subprocess, re, getpass, argparse, logging, time, binascii, struct
import ldap, ldap.sasl, ldap.modlist
import easygui

logging.basicConfig( level = logging.WARNING )

ADServer = "ldap://dc.fhcrc.org"
ADSearchBase = "dc=fhcrc,dc=org"
ADSearchScope = ldap.SCOPE_SUBTREE

__app__ = "New User Notifier"

homedir = os.path.expanduser("~")
cfgdir = os.path.join(homedir,'.newusers')
if not os.path.exists(cfgdir):
    os.makedirs(cfgdir)

def main():

##    if arguments.verbose:
##        log_format = '%(levelname)s:%(module)s:line %(lineno)s:%(message)s'
##        log_level = logging.INFO
##        logging.basicConfig(file=sys.stdout, format=log_format, level=log_level)

    if not l:
        print('no ldap ....')
        return False

    if args.debug:
        print('Debugging ....')
        print(args,l)

    if not args.config:
        if not setup():
            return False

    if args.searchdate:
        mytime=time.mktime(time.strptime(args.searchdate, "%Y%m%d"))
    else:
        mytime=time.time()

    cfgs = os.listdir(cfgdir)
    for c in args.config:
        config = c.replace(' ','_')
        if not config.endswith('.txt'):
            config=config+'.txt'
        if not config in cfgs:
            print('config file %s was not found.' % config)
            return False
        
        cfg = Settings(os.path.join(cfgdir,config))
        cfg.restore

        if args.debug:
            print(cfg.filter1_attr)
            print(cfg.filter1)
            print(cfg.filter2_attr)
            print(cfg.filter2)
            print(cfg.to)
            print(cfg.mailbody)
            print(cfg.run)

        users=getCreatedUsers(mytime,[[cfg.filter1_attr,cfg.filter1],
                                      [cfg.filter2_attr,cfg.filter2]])        
        if args.debug:
            print("getCreatedUsers(%s)=%s)" % (mytime, users))
        
        if len(users)==0:
            print("No new users found for the given date")
            return False        

        if args.debug:
            print('\n######### config: %s' % config)
        
        table = getUserAttrsTable(userlist=users)
        msg=cfg.mailbody+table2html(table,['sAMAccountName:HutchID','employeeID:EmplID',
                              'fhcrcpaygroup:Salary','division:Div'])
   
        print('\nSending notification email to %s !' % cfg.to)
        subject = __app__ + ' (' + config + ')'
        send_mail(cfg.to.split(','), subject, '<html>' + msg + '</html>')
                
def setup():
    
    msg = ("Welcome to the new employee notification tool.\n"
           "The tool allows you to send customized automated emails "
           "that contain information about all ActiveDirectory users "
           "created within the last 24h.\n"
           "You will be asked several questions and config filters. "
           "Searches may take a few seconds to complete.\n"
           )
    msg2 = ("\nPlease create a new filter or load an existing filter "
            "which you can then modify."
            )
    cfgs = os.listdir(cfgdir)
    if len(cfgs)==0:
        msg2 = ''
        easygui.msgbox(msg,__app__)
        pick='New Config'
    else:        
        pick = easygui.buttonbox(msg+msg2, __app__, ['New Config','Load Existing',
                                                     'Cancel'])
    if pick == 'Cancel':
        return False
    
    if pick != 'New Config':
        config = easygui.choicebox("Select an existing config:",__app__,cfgs)
        if not config:
            return False
        cfg = Settings(os.path.join(cfgdir,config))
        cfg.restore
    else:
        config=''
        while config == '':
            config = easygui.enterbox('Saving this filter. Please enter a name for this notification.', __app__)
            if not config:
                sys.exit()
        config=config.replace(' ','_')
        if not config.endswith('.txt'):
            config=config+'.txt'            
        cfg = Settings(os.path.join(cfgdir,config))
        cfg.store()    # persist the settings
        
        msg = ("Please select employee information you would like to filter.\n"
               "For example if you want to know about new staff in specific departments "
               "please pick 'Departments'. If you want to know about new users "
               "reporting to specific managers please pick 'Managers'. "
               "If you'd like to check for new users in specific Divisions and optionally "
               "filter by certain job titles please pick 'Divisions/Jobtitles'"
               )
        choi = [ "Departments", "Managers", "Divisions/Jobtitles" ]
        choival = [ "department", "manager", "division" ]

        pick = easygui.buttonbox(msg, __app__, choi)
        if not pick:
            return False
        idx = choi.index(pick)
        
        cfg.filter1=getUserAttrList (choival[idx])
        cfg.filter1_attr=choival[idx]

    cfg.filter1=easygui.multchoicebox(msg,"Select values from %s" % pick,cfg.filter1)
    if cfg.filter1_attr == 'division':
        alist=getUserAttrList ('title')
        filter2_attr='title'
        filter2=easygui.multchoicebox(msg,"Select values from 'Jobtitile'",alist)
    else:
        cfg.filter2_attr=''
        cfg.filter2=''

    msg = ("Please enter one or multiple email addresses (separated by comma) "
           "to which you want to send a notification when new users arrive"
           )
    cfg.to = easygui.enterbox(msg, __app__,cfg.to)


    msg = ("Please enter the email body you want to use for your notification "
           "email. A list of new users will be added below this text."
           )
    cfg.mailbody = easygui.textbox(msg, __app__, cfg.mailbody, codebox=False)

    msg = ("Optional: Please enter the command line of a script including full path "
           "and command options. This script will be executed when new users arrive.\n"
           "(Please leave this line empty to not execute anything.)"
           )
    cfg.run = easygui.enterbox(msg, __app__,cfg.run)
    
    cfg.store()    # persist the settings

    
    cmdline=''
    testdate=''
    out=''
    while True:
        if easygui.boolbox('Do you want to test this configuration (again) ?', __app__, ('Yes', 'No')):
            msg = ("If you want to test this config, please enter the creation date "
                         "(format: YYYYMMDD) you would like to test."
                        )
            testdate = easygui.enterbox(msg, __app__,testdate)
            if not testdate:
                break
            if testdate != '':
                cmdline = '%s --debug --search-date %s %s' % (getMyFile(),testdate,config)
                try:
                    out=subprocess.check_output(
                        cmdline,
                        stderr=subprocess.STDOUT,
                        shell=True)
                except subprocess.CalledProcessError, e:
                    print "subproces CalledProcessError.output = " + e.output
                easygui.codebox('Please see debugging output below:', __app__, out)
        else:
            break
    if cmdline != '':
        cmdline = '%s %s' % (getMyFile(),config)
        easygui.codebox('Please activate this command via cron:' , __app__,cmdline)
            
class Settings(easygui.EgStore):
    def __init__(self, filename):  # filename is required
        #-------------------------------------------------
        # Specify default/initial values for variables that
        # this particular application wants to remember.
        #-------------------------------------------------
        self.filter1_attr = ''
        self.filter1 = ''
        self.filter2_attr = ''
        self.filter2 = ''
        self.to = ''
        self.mailbody = ''
        self.run = ''

        #-------------------------------------------------
        # For subclasses of EgStore, these must be
        # the last two statements in  __init__
        #-------------------------------------------------
        self.filename = filename  # this is required
        self.restore()            # restore values from the storage file if possible
    
def getCreatedUsers(epoch,filters=[]):
    users=[]
    begin, end = getLastDayGM(epoch)
    if args.debug:
        print('######### getCreatedUsers GMT begin: %s, GMT end: %s' % (begin, end))
    ldapfilter = ( "(&(employeeID>=10000)(department=*)(title=*)(sAMAccountType=805306368)(whenCreated>=%s.0Z)" \
                   "(whenCreated<=%s.0Z)" % (begin, end))
    for filt in filters:
        filtstr = ''
        if filt[0] != '':
            for val in filt[1]:
                 filtstr = filtstr + '(' + filt[0] + '=' + cleanLDAP(val) + ')'
            if filtstr != '':
                filtstr = '(|' + filtstr + ')'
            ldapfilter=ldapfilter+filtstr
    ldapfilter=ldapfilter+')'
    
    #ldapfilter = ( "(&(employeeID>=10000)(department=*)(sAMAccountType=805306368)(whenCreated>=%s000000.0Z))" % args.searchdate)
    if args.debug:
        print('getCreatedUsers ldapfilter:',ldapfilter)
    #Attrs = [ "sAMAccountName", "uidNumber", "title", "department", "division", "displayName", "directReports", "manager", "fhcrcpaygroup", "ipPhone", "mail", "whenCreated"]
    Attrs = [ "sAMAccountName", ]
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    for result in Results:
        if not "sAMAccountName" in result[1]:
            continue
        users.append(result[1]["sAMAccountName"][0])
        #if args.debug:
            #print(result[1]["sAMAccountName"][0])
            #print(result[1]["department"][0])
            #print(result[1]["department"][0])
            #print(result[1]["division"][0])
            #print(result[1]["whenCreated"][0])
            #print('')
        
    return users


def table2html(mytable,headreplace=[]):
    t=(
    '<table border="1">\n'
    '<tr><th>'
    )
    t=t+'</th><th>'.join(mytable[0]['header'])
    t=t+'</th></tr>\n'
    #processing header replacements
    for hr in headreplace:
        s,r = hr.split(':')
        t=t.replace(s,r)
    for row in mytable[1].keys():
        t=t+'<tr><td>'
        t=t+row+'</td><td>'+'</td><td>'.join(mytable[1][row])
        t=t+'</td></tr>\n'
    t=t+'</table>\n'
    return t.replace('\n','')

def getLastDayGM(epoch):
    """ returns LDAP AD start end & end times (GMT) of a 24h period based on end time epoch"""
    return time.strftime('%Y%m%d%H%M%S', time.gmtime(epoch-86400)), \
            time.strftime('%Y%m%d%H%M%S', time.gmtime(epoch))

def cleanLDAP(mystr):
    mystr = mystr.replace( '\\', '\\5c' )
    mystr = mystr.replace( '(', '\\28' )
    mystr = mystr.replace( ')', '\\29' )
    return mystr
    
def getUserAttrList(attribute, userlist=[]):
    """ get a list of unique values from one user attribute from all users,
    optionally for a list of users """
    userfilter=""
    for username in userlist:
        userfilter = userfilter + "(sAMAccountName=" + username + ")"
    if userfilter != "":
        userfilter = "(|" + userfilter + ")"
    ldapfilter = ( "(&(employeeID>=10000)(sAMAccountType=805306368)%s)" % userfilter )
    if args.debug:
        print("*** getUserAttrLists %s ldapfilter:\n%s" % (attribute, ldapfilter))
    Attrs = []
    Attrs.append(attribute)
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    attrlist = []
    for result in Results:
        if not attribute in result[1]:
            continue
        attrlist.append(result[1][attribute][0])
    return sorted(uniq(attrlist))

def getUserAttrsTable(attributes=[], userlist=[]):
    """ get a table of multiple attribute values for a list of users or all users
        the table consists of a list of 2 dictionaries: The first consists of a header
        which is a list of attributes saved under a dictionary key called 'header'.
        The second directionary constists of sAMAccountName keys and each contains
        a list of values.        
    """
    userfilter=""
    for username in userlist:
        userfilter = userfilter + "(sAMAccountName=" + username + ")"
    if userfilter != "":
        userfilter = "(|" + userfilter + ")"
    ldapfilter = ( "(&(employeeID>=10000)(sAMAccountType=805306368)%s)" % userfilter )
    if args.debug:
        print("*** getUserAttrsTable %s ldapfilter:\n%s" % (attributes, ldapfilter))
    Attrs = attributes
    if len(Attrs) == 0:
        Attrs = [ "displayName", "employeeID", "manager", "title", 
                "department", "division", "fhcrcpaygroup", "mail", "ipPhone"]
    if 'sAMAccountName' in Attrs:
        Attrs.remove('sAMAccountName')
    Attrs.insert(0,'sAMAccountName')
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    table = [{},{}]
    table[0]['header'] = Attrs    
    for result in Results:
        if len(result[1]) == 1:
            continue
        row=[]
        key=''
        newattr=[]
        for attr in Attrs:
            if result[1].has_key(attr):
                #if args.debug:
                    #print(attr)
                    #print('attr content:', result[1][attr])                
                if attr == 'manager':
                    row.append(getAttr(l, result[1][attr][0], ['sAMAccountName',])[0])            
                elif attr == 'sAMAccountName':
                    key=result[1][attr][0]                
                else:
                    row.append(result[1][attr][0])
            else:
                row.append('')                
        if key != '':            
            table[1][key]=row
    return table

def groupGetMembers(l,samname):
    members=[]
    dn=groupGetDN(l,samname)
    ldapfilter = ( "(&(memberof=%s))" % dn
               )
    #Attrs = [ "displayName", "directReports", "manager", "sAMAccountName", "title", "department", "division", "fhcrcpaygroup" ]
    Attrs = [ "sAMAccountName", ]
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    for result in Results:
        if not "sAMAccountName" in result[1]:
            continue
        members.append(result[1]["sAMAccountName"][0])
    return members

def userMemberOf(l,samname):
    groups=[]
    #return groupGetMembers(l,samname)
    dn=userGetDN(l,samname)
    attrlist=getAttrList(l, dn, ['memberOf',])
    for group in attrlist[0]:
        groups.append(getAttr(l,group,["sAMAccountName"],)[0])
    return groups
    
def setGroupAttr(l,samOrDn, attr, value):
    if not samOrDn.lower().startswith('cn='):
        samOrDn = groupGetDN(l, samOrDn)
    myattr = [(ldap.MOD_REPLACE, attr, value)]
    try:
        l.modify_s(samOrDn, myattr)
    except ldap.LDAPError, err:
        errstr = err[0]['desc']
        print "Error setting %s to '%s' in group %s: %s" % (attr, value, samOrDn, errstr)
        return False    
    return True
    
def groupGetDN(l,samname):
    ldapfilter = '(&(objectCategory=group)(sAMAccountName=%s))' % samname
    Attrs = ['distinguishedName']
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    return Results[0][0]

def userGetDN(l,samname):
    ldapfilter = '(&(sAMAccountType=805306368)(sAMAccountName=%s))' % samname
    Attrs = ['distinguishedName']
    r = l.search( ADSearchBase, ADSearchScope, ldapfilter, Attrs )
    Type, Results = l.result( r, 60 )
    return Results[0][0]
                          
def getAttr(l, dn, attrs):
    dn = dn.replace( '\\', '\\5c' )
    dn = dn.replace( '(', '\\28' )
    dn = dn.replace( ')', '\\29' )
    filter = ( "(distinguishedName=" + dn + ")" )
    q = l.search( ADSearchBase, ADSearchScope, filter, attrs)
    namesearch = l.result( q, 60 )[1]
    result=[]
    if namesearch[0][0]:
        for attr in attrs:
            if namesearch[0][1].has_key(attr):
                result.append(namesearch[0][1][attr][0])
    return result

def getAttrList(l, dn, attrs):
    dn = dn.replace( '\\', '\\5c' )
    dn = dn.replace( '(', '\\28' )
    dn = dn.replace( ')', '\\29' )
    filter = ( "(distinguishedName=" + dn + ")" )
    q = l.search( ADSearchBase, ADSearchScope, filter, attrs)
    namesearch = l.result( q, 60 )[1]
    result=[]
    if namesearch[0][0]:
        for attr in attrs:
            if namesearch[0][1].has_key(attr):
                result.append(namesearch[0][1][attr])
    return result


def sid2str(sid):
    """ convert an active directory sid as returned by
    python-ldap into a string that can be used as an LDAP query value """
    # convert to string if a list has been passed.
    if hasattr(sid, '__iter__'):
        sid=sid[0]
    srl = ord(sid[0])
    number_sub_id = ord(sid[1])
    iav = struct.unpack('!Q','\x00\x00'+sid[2:8])[0]
    sub_ids = [
        struct.unpack('<I',sid[8+4*i:12+4*i])[0]
        for i in range(number_sub_id)
        ]
    return 'S-%d-%d-%s' % (
        srl,
        iav,
        '-'.join([str(s) for s in sub_ids]),
        )

def sidstr2gid(sidstr):
    """ convert an active directory sid string to a valid gid number
    for posix permission management"""
    m = re.search(r'\d+$', sidstr)
    return int(m.group())+100000

def getMyFile():
    try:
        myFile = os.path.abspath( __file__ )
    except:
        #if hasattr(sys,"frozen") and sys.frozen == "windows_exe": ... does not work
        myFile = os.path.abspath(sys.executable)
    return myFile

def uniq(seq):
   # Not order preserving
   keys = {}
   for e in seq:
       keys[e] = 1
   return keys.keys()


def ldapinit():
    try:
        l = ldap.initialize( ADServer )
        l.set_option(ldap.OPT_REFERRALS, 0)
        if sys.platform == 'win32':
            l.simple_bind_s( args.binddn, args.bindpw )
        else:
            auth = ldap.sasl.gssapi("")
            l.sasl_interactive_bind_s("", auth)
        return l
    except ldap.LOCAL_ERROR, err:
        errstr = err[0]['info']
        print ("Error logging into LDAP: %s" % errstr)
        if errstr.find('Credentials cache file'):
            print ("*** Please execute kinit to authenticate and then run this script again! ***")
        return None
    except ldap.LDAPError, err:
        errstr = err[0]['desc']
        print "LDAP Error: %s" % errstr
        return None

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
        if sys.platform == 'win32':
            smtphost = 'mx'
        else:
            smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')

    try:
        base = os.path.basename(__file__)
    except NameError:  # We are the main py2exe script, not a module
        base = os.path.basename(sys.argv[0])
        
    if fromaddr == '':
        fromaddr = base + '-no-reply@' + \
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
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=base)

    if text.startswith('<html>') or text.startswith('<table>'):
        full_body=full_body.replace('\n','<br>')
        message.attach(MIMEText(full_body,'html'))
    else:
        message.attach(MIMEText(full_body,'plain'))

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

def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='onboarding-staff',
        description='send notifications to helpdesk to create scientific computing ' + \
            'resources when new accounts are found in active directory')
    parser.add_argument( 'config', type=str, default=[], nargs='*',
        help="a config setting that has been saved before")
    parser.add_argument( '--debug', '-d', dest='debug', action='store_true', default=False,
        help="do not send an email but print the result to  console")
    parser.add_argument('--search-date', '-s', dest='searchdate', action='store', 
        #default=time.strftime('%Y%m%d', time.localtime()),
        default=None,
        help='instead of using today\'s date use this date for debugging purpose. ' \
            'format: YYYYMMDD ')
    parser.add_argument('--mailto', '-m', dest='mailto', action='store', default='', 
        help='send email to this helpdesk address.')
    parser.add_argument( '--binddn', type=str, default='ldapsc@fhcrc.org',
        help='bind name for AD' )
    parser.add_argument( '--bindpw', type=str, default='MyPassword',
        help='password for binddn' )
    
    return parser.parse_args()

if __name__=="__main__":
    args = parse_arguments()
    l = ldapinit()
    sys.exit(main())
