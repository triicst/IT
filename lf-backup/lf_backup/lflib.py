# lffunc: helper functions lf-backup

import sys,os,re,tempfile,getpass,socket,optparse
import subprocess

from swiftclient import shell
from swiftclient import RequestException
from swiftclient.exceptions import ClientException
from swiftclient.multithreading import OutputManager

from swiftclient import Connection

# wrapper functions for swiftclient shell functions

def upload_folder_to_swift(fname,swiftname,container,meta=""):
    oldout = sys.stdout
    olderr = sys.stderr
    outfile = 'Swift_upload_'+container+'_'+swiftname.rstrip('/').replace('/','_')+".log"
    outpath = os.path.join(tempfile.gettempdir(),outfile)
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("upload logging to %s" % outpath)
    print("uploading to %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen(gettailcmd(outpath))
    upload_to_swift(fname,swiftname,container,meta)
    print("upload logged to %s" % outpath)
    print("SUCCESS: %s uploaded to %s/%s" % (fname,container,swiftname))
    sys.stdout = oldout
    sys.stderr = olderr
    fh.close()

def download_folder_from_swift(fname,swiftname,container):
    oldout = sys.stdout
    olderr = sys.stderr
    outfile = 'Swift_download_'+container+'_'+swiftname.rstrip('/').replace('/','_')+".log"
    outpath = os.path.join(tempfile.gettempdir(),outfile)
    fh = open(outpath, 'w')
    sys.stdout = fh
    sys.stderr = fh
    print("download logging to %s" % outpath)
    print("downloading from %s/%s, please wait ....." % (container,swiftname))
    sys.stdout.flush()
    tailpid=subprocess.Popen(gettailcmd(outpath))
    sw_download('--prefix='+swiftname,
        '--output-dir='+fname,
        '--remove-prefix',
        container)
    print("download logged to %s" % outpath)
    print("SUCCESS: %s/%s downloaded to %s" % (container,swiftname,fname))
    sys.stdout = oldout
    sys.stderr = olderr
    fh.close()

USERNAME = getpass.getuser()
OS = sys.platform
IP = socket.gethostbyname(socket.gethostname())
    
_default_global_options = {
    "segment_size": '1073741824',
    "use_slo": True,
    "changed": True,
    "auth_version": os.environ.get('ST_AUTH_VERSION',(os.environ.get('OS_AUTH_VERSION','1.0'))),
    "auth": os.environ.get('ST_AUTH', 'https://tin.fhcrc.org/auth/v1.0'),
    "user": os.environ.get('ST_USER', USERNAME),
    "key": os.environ.get('ST_KEY', ''),
    "retries": 5,
    "os_username": os.environ.get('OS_USERNAME', USERNAME),
    "os_password": os.environ.get('OS_PASSWORD', ''),
    "os_tenant_id": os.environ.get('OS_TENANT_ID'),
    "os_tenant_name": os.environ.get('OS_TENANT_NAME', ''),
    "os_auth_url": os.environ.get('OS_AUTH_URL', 'https://tin.fhcrc.org/auth/v2.0'),
    "os_auth_token": os.environ.get('OS_AUTH_TOKEN'),       
    "os_storage_url": os.environ.get('OS_STORAGE_URL'),  
    "os_region_name": os.environ.get('OS_REGION_NAME', 'default'),
    "os_service_type": os.environ.get('OS_SERVICE_TYPE'),
    "os_endpoint_type": os.environ.get('OS_ENDPOINT_TYPE'),        
}

def shell_minimal_options():

   parser = optparse.OptionParser()

   parser.add_option('-A', '--auth', dest='auth',
      default=_default_global_options['auth'])
   parser.add_option('-V', '--auth-version',
      default=os.environ.get('ST_AUTH_VERSION',
         (os.environ.get('OS_AUTH_VERSION','2.0'))))
   parser.add_option('-U', '--user', dest='user',
      default=_default_global_options['user'])
   parser.add_option('-K', '--key', dest='key',
      default=_default_global_options['key'])

   parser.add_option('--os_auth_token',default=_default_global_options['os_auth_token'])
   parser.add_option('--os_storage_url',default=_default_global_options['os_storage_url'])

   parser.add_option('--os_username', default=_default_global_options['os_username'])
   parser.add_option('--os_password', default=_default_global_options['os_password'])
   parser.add_option('--os_auth_url', default=_default_global_options['os_auth_url'])

   parser.add_option('--os_user_id')
   parser.add_option('--os_user_domain_id')
   parser.add_option('--os_user_domain_name')
   parser.add_option('--os_tenant_id')
   parser.add_option('--os_tenant_name',default=_default_global_options['os_tenant_name'] )
   parser.add_option('--os_project_id')
   parser.add_option('--os_project_domain_id')
   parser.add_option('--os_project_name')
   parser.add_option('--os_project_domain_name')
   parser.add_option('--os_service_type')
   parser.add_option('--os_endpoint_type')
   parser.add_option('--os_region_name', default=_default_global_options['os_region_name'])

   # new mandatory bogosity required for swiftclient >= 3.0.0
   parser.add_option('--debug')
   parser.add_option('--info')
   
   parser.add_option('-v', '--verbose', action='count', dest='verbose',
       default=1, help='Print more info.')

   return parser

def sw_shell(sw_fun,*args):

   if _default_global_options['os_auth_token'] and _default_global_options['os_storage_url']:
      args=args+("--os_auth_token",_default_global_options['os_auth_token'],
         "--os_storage_url",_default_global_options['os_storage_url'])

   args = ('',) + args
   with OutputManager() as output:
      parser = shell_minimal_options()
      try:
         sw_fun(parser, list(args), output)
      except (ClientException, RequestException, socket.error) as err:
         output.error(str(err))
 
def sw_download(*args):
    sw_shell(shell.st_download,*args)
 
def sw_upload(*args):
    sw_shell(shell.st_upload,*args)

def sw_post(*args):
    sw_shell(shell.st_post,*args)

def upload_to_swift(filename,destname,container,meta=""):
    final=[container,filename]
    if meta:
        final=meta+final
    sw_upload("--object-name="+destname,
        "--segment-size="+_default_global_options['segment_size'],
        "--use-slo",
        "--changed",
        "--segment-container=.segments_"+container,
        "--header=X-Object-Meta-Uploaded-by:"+getpass.getuser(),*final)

# imported code to create connections to allow get_container calls

def create_sw_conn():
   swift_auth=_default_global_options['auth']
   swift_auth_token=_default_global_options['os_auth_token']
   storage_url=_default_global_options['os_storage_url']

   if swift_auth_token and storage_url:
      return Connection(preauthtoken=swift_auth_token,preauthurl=storage_url)

   if swift_auth:
      swift_user=os.environ.get("ST_USER")
      swift_key=os.environ.get("ST_KEY")

      if swift_user and swift_key:
         return Connection(authurl=swift_auth,user=swift_user,key=swift_key)

   print("Error: Swift environment not configured!")
   sys.exit()

def get_sw_container(container):
    objs=''

    swift_conn=create_sw_conn()
    if swift_conn:
        try:
            headers,objs=swift_conn.get_container(container,full_listing=True)
        except ClientException:
            print("Error: cannot access Swift container '%s'!" % container)
            sys.exit()

        swift_conn.close()

    return objs

# end swift stuff 

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

def send_mail(
        to,
        subject,
        text,
        attachments=[],
        cc=[],
        bcc=[],
        smtphost="",
        fromaddr=""):

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

    if not isinstance(to, list):
        print("the 'to' parameter needs to be a list")
        return False
    if len(to) == 0:
        print("no 'to' email addresses")
        return False

    myhost = socket.getfqdn()

    if smtphost == '':
        smtphost = get_mx_from_email_or_fqdn(myhost)
    if not smtphost:
        sys.stderr.write('could not determine smtp mail host !\n')

    if fromaddr == '':
        fromaddr = os.path.basename(__file__) + '-no-reply@' + \
            '.'.join(myhost.split(".")[-2:])  # extract domain from host
    tc = 0
    for t in to:
        if '@' not in t:
            # if no email domain given use domain from local host
            to[tc] = t + '@' + '.'.join(myhost.split(".")[-2:])
        tc += 1

    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = COMMASPACE.join(to)
    message['Date'] = formatdate(localtime=True)
    message['Subject'] = subject
    message['Cc'] = COMMASPACE.join(cc)
    message['Bcc'] = COMMASPACE.join(bcc)

    body = Template(
        'This is a notification message from $application, running on \n' +
        'host $host. Please review the following message:\n\n' +
        '$notify_text\n\n')
    host_name = socket.gethostname()
    full_body = body.substitute(
        host=host_name.upper(),
        notify_text=text,
        application=os.path.basename(__file__))

    message.attach(MIMEText(full_body))

    for f in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            'attachment; filename="%s"' %
            os.path.basename(f))
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
