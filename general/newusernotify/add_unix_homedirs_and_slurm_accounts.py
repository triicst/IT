#! /usr/bin/env python3

"""
if new users are detected this script drops their 5 digit uidNumbers into
a folder where another script triggers the creation of posix home
directories.
Users that do not have an email address and users with job descriptions 
in list titignoreset are ignored.
"""

import sys, os, argparse, json, requests, subprocess

mailusers = ['cit-sc',]
mailerrorusers = ['petersen',]
tmpdir = '/var/tmp'

# job titles that do not require an account. 
titignore = ["Program Assistant", "Project Coordinator", 
             "Administrative Assistant", "Administrative Coordinator", 
             "Office Worker", "Data Operations Manager", 
             "Clinical Research Coordinator", "Administrative Manager", 
             "Data Entry Operator", "Clinical Research Nurse", 
             "Veterinary Technician", "Animal Equipment Preparer", 
             "Program Administrator", "Senior Project Manager", 
             "Coordinating Center Manager", "Animal Technician", 
             "Member Emeritus", "Nurse Manager", "Financial Analyst", 
             "Yoga Teacher", ""]

# the user database of potential scientific computing users
j = requests.get('https://toolbox.fhcrc.org/json/sc_users.json').json()


def main():

    if not os.path.exists(args.dir):
        print ('Output directory %s does not exist' % args.dir)
        return False

    # adding users #########################################

    uids = uniq(jget(j, 'employeeID'))
    uids_add, uids_del = listcompare('%s/uids_last.json' % tmpdir, uids)
    uids_add_filt = []

    # adding new users but never more than 1000
    x = len(uids_add) - 1
    if x > 100: x = 100
    print("\nChecking %s users...:" % len(uids_add), uids_add[0:x])
    n = 1
    if len(uids_add) <= 1000:
        for uid in uids_add:
            print('%s: %s' % (n,uid))
            # ignore some jobtitles 
            if jsearchone(j,"employeeID",uid,"mail") == "" or jsearchone(j,"employeeID",uid,"title") in titignore:
                continue

            uids_add_filt.append(uid)
            with open(os.path.join(args.dir,str(uid)), 'w') as outfile:
                outfile.write('create a homedir')
            n+=1

        # attempt to create a slurm account             
        slurmerr = []
        for uidNumber in uids_add_filt:
            username = jsearchone(j,"employeeID",uidNumber,"uid")
            j1 = requests.get('https://toolbox.fhcrc.org/mapaccount/rest/%s' % username).json()            
            if len(j1[username]) > 0:
                PI = j1[username][0]
                #print('PI:', j1[username][0])
                ret = subprocess.run("sacctmgr -i create user %s account=%s defaultaccount=%s" % (username, PI, PI), shell=True).returncode
                if ret:
                    slurmerr.append(username)
                    
        
        if len(uids_add_filt) > 0:
            mailnewusers(j, uids_add_filt, slurmerr)
            
    else:
        print('Error: will not add batches of more than 1000 users')

	## deleting diabled users but never more than 10
	#print("\nDeleting %s users...:" % len(uids_del),uids_del)
	#if len(uids_del) <= 10: 
		#for uid in uids_del:
			#print('test: del user %s' % uid)
			#break
			#s = 'pveum userdel %s@FHCRC.ORG ' % uid
			#ret = run_script(s, output=True)
			#if ret > 0:
				#print('******** Error : %s' % ret)
	#else:
		#print('Error: will not delete more than 1000 users at a time')

	# save the list of currently processed uids 

    with open('%s/uids_last.json' % tmpdir, 'w') as outfile:
        json.dump(uids, outfile)


########################################################################

# some helper functions

def mailnewusers(j, uids_add, slurmerr):
    
    body = ''
    if len(slurmerr) > 0:
        body = 'Slurm accounts could NOT be created for users: %s' % ", ".join(slurmerr)
        
    print('notify on uids:', uids_add)
    rows = []
    for uid in uids_add:
        row = jgetonerow(j, "employeeID", uid)
        rows.append(row)
    
    body = body + '\n\n' + json.dumps(rows, sort_keys=True, indent=4)    
    #body = json2htm (body)
        
    try:
        send_mail(mailusers, "created new Unix home dirs for %s users(s)" % len(uids_add),
                body)

    except:
        e=sys.exc_info()[0]
        sys.stderr.write("Error in send_mail while sending to '%s': %s\n" % (mailerrorusers[0], e))
        send_mail(mailerrorusers, "Error - unix-homedirs",
                "Please debug email notification to user '%s', Error: %s\n" % (mailerrorusers[0], e))

def listcompare(oldjsonfile,newlist):
	""" compares a list with a previously saved list and returns
	    a list of newly add items and a list of removed items.
	"""
	addedlist, removedlist = newlist, []
	if os.path.exists(oldjsonfile):
		with open(oldjsonfile, 'r') as f:
			oldlist=json.load(f)
			addedlist = [item for item in newlist if item not in oldlist]
			removedlist = [item for item in oldlist if item not in newlist]
	return addedlist, removedlist

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


def json2htm(j):
    htmlresult = """<table>
                     <thead>
                 <tr>"""    
    for var in json["head"]["vars"]:
        htmlresult += "<th>%s</th>" % var
        
    htmlresult += "</tr></thead><tbody>"

    for result in json["results"]["bindings"]:
        htmlresult += "<tr>"
    for var in json["head"]["vars"]:
        if result[var]["value"]:
            htmlresult += "<td>%s</td>" % result[var]["value"]
    htmlresult += "</tr>"
    htmlresult +="""
                </tbody>
                </table>
                """
    return htmlresult


class ScriptException(Exception):
    def __init__(self, returncode, stdout, stderr, script):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        Exception.__init__('Error in script')

def run_script(script, output=True, stdin=None):
    """Returns (stdout, stderr), raises error on non-zero return code"""
    # Note: by using a list here (['bash', ...]) you avoid quoting issues, as the 
    # arguments are passed in exactly this order (spaces, quotes, and newlines won't
    # cause problems):
    stdout = ""
    for line in script.split('\n'):
        if output:
            try:
                if line:
                    print("************* Executing command: %s" % line)
                    stdout = subprocess.call(line,shell=True)
            except:
                print("Error executing command: %s" % line)
                print("Error: %s" % stdout)
        else:
            proc = subprocess.Popen(['bash', '-c', line],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode:
                raise ScriptException(proc.returncode, stdout, stderr, script)
    return stdout


def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):
    """ sends email, perhaps with attachment """

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
            '$notify_text\n\n'
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
    import re
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
    parser = argparse.ArgumentParser(prog='add_unix_homedirs',
        description='a tool for deploying resources from proxmox ' + \
            '(LXC containers or VMs)')
    #parser.add_argument( 'command', type=str, default='deploy', nargs='?',
        #help="a command to be executed. (deploy, start, stop)")
    #parser.add_argument('--hosts', '-n', dest='hosts', action='store', default=[],  nargs='*',
        #help='hostnames of your new VM/containers')
    parser.add_argument('--dir', '-d', dest='dir', action='store', default='', 
        help='output directory for uid stub files')    
    #parser.add_argument( '--debug', '-d', dest='debug', action='store_true', default=False,
        #help="do not send an email but print the result to  console")
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
