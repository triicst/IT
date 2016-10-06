#! /usr/bin/env python

# Script to clone/update all public github repositories that a user or organization owns or watches
# repositories are shared by default allowing access to all members of a unix group 
# an email address can be notified about uncommitted changes in one of the repositories
#
# github-syncer dirkpetersen / June 2014

import requests, json
import sys, os, subprocess, argparse, glob, re

def main():

    currdir = os.getcwd()

    # Parse command-line arguments
    arguments = parse_arguments()
        
    if arguments.watched:
        r = requests.get("https://api.github.com/users/%s/subscriptions?per_page=100" % (arguments.user))
    else:
        r = requests.get("https://api.github.com/users/%s/repos?per_page=100" % (arguments.user))
            # or repos?per_page=100&page=2

    repos = json.loads(r.content)

    urls = [repo['clone_url'] for repo in repos]
    ssh_urls = [repo['ssh_url'] for repo in repos]
    names = [repo['name'] for repo in repos]

    shared = ' --shared'
    if arguments.single:
        shared = ''        
    if arguments.dir != '':
        os.chdir(os.path.expanduser(arguments.dir))
        if os.getcwd() != os.path.expanduser(arguments.dir):
            print('could not change to directory: %s ! Current dir: %s  Exiting!' % (os.path.expanduser(arguments.dir),os.getcwd()))
            return 1
        if arguments.debug:
            print("***** DEBUG: Changed to dir: %s" % os.path.expanduser(arguments.dir))
            
    # Clone/update them all
    name = ''
    for url in urls:
        name = names[urls.index(url)]
        ssh_url = ssh_urls[urls.index(url)]
        cmd=''
        if name == 'Oncoscape':
            print('ignoring Oncoscape')
            continue # for some reason always errors in Oncoscape
        if os.path.isdir(name+'/.git'):
            cmd = 'cd %s; git remote set-url origin %s; ' % (name,url)
            cmd = cmd + 'git pull origin master; '
            print("   updating repository %s ..." % name)
        else:            
            if arguments.single:                
                cmd = 'git clone %s' % url
                print("   cloning repository %s ..." % name)
            else:
                cmd = 'git init --shared %s; cd %s; ' % (name, name)
                cmd = cmd + 'git remote add origin %s; ' % url
                cmd = cmd + 'git config branch.master.remote origin; '
                cmd = cmd + 'git config branch.master.merge refs/heads/master; '
                cmd = cmd + 'git pull origin master; '
                print("   pulling shared repository %s ..." % name)
        if not arguments.no_ssh_url:
            cmd = cmd + 'git remote set-url origin %s; ' % ssh_url
        cmd = cmd + 'git diff > ../%s.changes.txt; unix2dos -q ../%s.changes.txt; cd .. ; ' % (name, name)
        if not arguments.single:
            cmd = cmd + 'chmod -fR g+rw %s; ' % name        
        oldmask = os.umask(arguments.umask)
        if arguments.debug:
            print("***** DEBUG: Executing commands: %s" % cmd)        
        pipe = subprocess.Popen(cmd, shell=True)
        pipe.wait()
        os.umask(oldmask)
        # remove any zero bytes files 
        if os.stat("%s.changes.txt" % name).st_size == 0:
            os.remove("%s.changes.txt" % name)
                
    # send email if requested via --email-notify
    if arguments.email != '':
        send_files = glob.glob('*.changes.txt')
        if len(send_files) > 0:
            if arguments.debug:
                print("***** DEBUG: uncommitted changes files to send :\n %s" % ', '.join(send_files))
            try:
                send_mail([arguments.email,], "Please commit GITHUB changes for '%s' !" % arguments.user,
                        "Please see attached uncommitted changes for github account '%s'.\n\n" \
                        "Check folder %s . \n\nIf the repository is out of sync because you " \
                        "accidentially deleted a file you can bring the repository back in sync by " \
                        "executing 'git push; git reset --hard' " % (arguments.user, os.getcwd()),send_files)
                print ('\nSent uncommitted changes (%s) to %s' % (', '.join(send_files),arguments.email))                
            except:
                print("Error in main")
                send_mail([arguments.email,], "Error - github-syncer",
                    "Error - please debug email notification in script github-syncer\n")

    # print example line
    if name:
        reposdir = name
        if arguments.dir != '':
            reposdir = "%s/%s" % (arguments.dir,name)
        print ("\nFinished cloning/updating %d public repos for %s!:" % (len(urls),arguments.user))
        print ("for example, to upload %s to github run this command:" % name)
        print ("cd %s; git commit -a; git push " % reposdir)
    else:
        print ("Nothng to do !!!")

    os.chdir(currdir)

def send_mail(to, subject, text, attachments=[], cc=[], bcc=[], smtphost="", fromaddr=""):

    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEBase import MIMEBase
    from email.MIMEText import MIMEText
    from email.Utils import COMMASPACE, formatdate
    from email import Encoders
    from string import Template
    import socket
    import smtplib
    
    if not to:
        print("no 'to' email address")
        return False
    files=attachments  #attachments.split()
    tolist=to   #to.split()
    #assert type(bcc)==list

    if smtphost == '':
        smtphost = get_mx_from_email(to[0])
    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
           '.'.join(smtphost.split(".")[-2:]) #extract domain from host
    
    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(tolist)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)

    body = Template('This is a notification message from $application, running on \n' + \
            'host $host. Please review the following message:\n\n' + \
            '$notify_text\n\nIf output is being captured, you may find additional\n' + \
            'information in your logs.\n'
            )
    host_name = socket.gethostname()
    full_body = body.substitute(host=host_name.upper(), notify_text=text, application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        message.attach(part)

    addresses = []
    for x in tolist:
        addresses.append(x)
    for x in cc:
        addresses.append(x)
    for x in bcc:
        addresses.append(x)

    smtp = smtplib.SMTP(smtphost)
    smtp.sendmail(fromaddr, addresses, message.as_string())
    smtp.close()

    return True

def get_mx_from_email(addr):
    """retrieve the first mail exchanger dns name from an email address."""
    # Match the mail exchanger line in nslookup output.
    MX = re.compile(r'^.*\s+mail exchanger = (?P<priority>\d+) (?P<host>\S+)\s*$')
    # Find mail exchanger of this address.
    host = addr.rsplit('@', 2)[1]
    p = os.popen('nslookup -q=mx %s' % host, 'r')
    mxes = list()
    for line in p:
        m = MX.match(line)
        if m is not None:
            mxes.append(m.group('host')[:-1])  #[:-1] just strips the ending dot
    if len(mxes) == 0:
        return False
    else:
        return mxes[0]

def parse_arguments():
    """
    Gather command-line arguments.
    """

    parser = argparse.ArgumentParser(prog='github-syncer',
        description='clone or update all public github repositories that a user or ' + \
        'organization owns or watches.')
    parser.add_argument( '--watched', '-w', dest='watched', action='store_true',
        help='use watched repositories instead of owned ones',
        default=False )
    parser.add_argument( '--single', '-s', dest='single', action='store_true',
        help='the repository will not be initialized in --shared mode',
        default=False )
    parser.add_argument( '--no-ssh-url', '-n', dest='no_ssh_url', action='store_true',
        help='do not set the remote url to git@github.com:xxx for ssh auth after each run',
        default=False )
    parser.add_argument( '--debug', '-g', dest='debug', action='store_true',
        help='show the actual shell commands that are executed (git, chmod, cd)',
        default=False )
    parser.add_argument( '--email-notify', '-e', dest='email',
        action='store',
        help='notify this email address of any uncommitted changes ',
        default='' )        
    parser.add_argument( '--umask', '-m', dest='umask',
        action='store',
        type=int,
        help='temporarily set the umask for repositories setup in shared mode (default=0002)',
        default=0002 )    
    parser.add_argument( '--dir', '-d', dest='dir',
        action='store', 
        help='root directory where repositories will be created or updated',
        default='' )
    parser.add_argument( '--user', '-u', dest='user',
        action='store', 
        help='github user or organization'
        )
    args = parser.parse_args()
    if not args.user:
        parser.error('required option --user not given !')
    if args.debug:
        print('***** DEBUG: arguments name space ')
        print(args)
        
    return args

if __name__ == '__main__':
    sys.exit(main())
