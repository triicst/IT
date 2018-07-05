#! /usr/bin/env python3

## add new scientific departments from PS_DEPT_TBL to SC_CostCenters, criteria:
#  (SOURCE.DESCR LIKE '%Lab%' OR
#   SOURCE.DESCR LIKE '%Studies%') AND
#  SOURCE.COMPANY <> 'CCA' AND
#  SOURCE.EFFDT > '1/1/2017'

import sys, os, pymssql, requests, csv, json, collections, re

mailto = 'cit-sc@fredhutch.org'

def main():

	with open('/root/sqlcreds', 'r') as f:
		server,database,user,password = f.readline().strip().split(':')

	conn=pymssql.connect(server=server, user=user, password=password, database=database)

	# *********************** SC_CostCenters updates *****************************

	cursor = conn.cursor()
	try:
		cursor.execute("""
		MERGE SC_CostCenters AS TARGET
		USING PS_DEPT_TBL AS SOURCE 
		ON (TARGET.dept_id = SOURCE.DEPTID) 
		--When records are matched, update 
		--the records if there is any change
		WHEN MATCHED THEN 
		UPDATE SET TARGET.department = SOURCE.DESCR
		--When no records are matched, insert
		--the incoming records from source
		--table to target table
		WHEN NOT MATCHED BY TARGET AND
		  (SOURCE.DESCR LIKE '%Lab%' OR
			SOURCE.DESCR LIKE '%Studies%') AND
		  SOURCE.COMPANY <> 'CCA' AND
		  SOURCE.EFFDT > '7/1/2018'
		THEN INSERT (dept_id, pi_dept, dept_manager, department)
		VALUES (SOURCE.DEPTID, SOURCE.DESCRSHORT, '', SOURCE.DESCR)
		--When there is a row that exists in target table and
		--same record does not exist in source table
		--then delete this record from target table
		WHEN NOT MATCHED BY SOURCE THEN 
		DELETE;
		""" 
		)
	except pymssql.Error as e:
	   print ("SQL Error: "+str(e))
	   send_mail([mailto,], "ac_add_new_depts.py failed." , 
	   "This script adds new departments to table SC_CostCenters and it failed with this error message:\n %s" % str(e))
	   
	conn.commit()
	conn.close()
	
	return True

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

if __name__ == '__main__':        
    sys.exit(main())
