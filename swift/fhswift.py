#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fhswift is a module that allows users to easily move data to and from 
the swift object store at Fred Hutch. 

to test, run this in a python shell:

import fhswift
tests()

"""

import sys, os, optparse, urllib.request, getpass, socket
import swiftclient, keystoneclient
from swiftclient import shell
from swiftclient import RequestException
from swiftclient.exceptions import ClientException
from swiftclient.multithreading import OutputManager
from swiftclient.service import SwiftService # a new way of using swift 

class KeyboardInterruptError(Exception): pass

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

def tests():
    print ('######  Running tests !!! ########')
    # first we build a list of meta data 
    metadata = []
    metadata = meta_add(metadata, 'project', 'important project')
    metadata = meta_add(metadata, 'cancer', 'lung')
    # upload a folder to container 'fhswift_testcases with prefix 'samba-test'
    upload_folder('/var/log/samba', 'samba-test', 'fhswift_testcases', metadata)
    # download objects with prefix 'samba-test' from container 'fhswift_testcases'
    download_folder('/tmp/fhswift_testcases','samba-test','fhswift_testcases')
    # get a list of objects with prefix 'samba-test' from container 
    obj_list=list_container('fhswift_testcases', 'samba-test')
    # loop through list and delete each object
    for obj in obj_list:
        sw_delete('fhswift_testcases', obj)
    # finally also delete the container
    sw_delete('fhswift_testcases')

def upload_folder(fname,objectname,container,meta):
    final=[container,fname]
    if meta:
        final=meta+final
    sw_upload("--object-name="+objectname,
        "--segment-size="+_default_global_options['segment_size'],   # should be _default_global_options['segment_size'] but is not working
        "--use-slo",
        "--changed",
        "--segment-container=.segments_"+container,
        "--header=X-Object-Meta-Uploaded-by:"+USERNAME,*final)
    print("SUCCESS: %s uploaded to %s/%s" % (fname,container,objectname))

def download_folder(fname,objectname,container):
    sw_download('--prefix='+objectname,
        '--output-dir='+fname,
        '--remove-prefix',
        container)
    print("SUCCESS: %s/%s downloaded to %s" % (container,objectname,fname))
    
def list_container(container, prefix):
    obj_list = []
    myoptions={'prefix': prefix}
    stats=SwiftService(options=_default_global_options).stat()
    if not stats["success"] == True:
        print('not authenticated')
        return False
    with SwiftService(options=_default_global_options) as swift:
        listing=swift.list(container=container, options=myoptions)
        for o in listing:
            for i in o['listing']:
                obj_list.append(i['name'])
        return obj_list
        
def checkAuthServer():
    """ Check if swift auth server is reachable """
    url=_default_global_options['os_auth_url']
    if not url:
        url=_default_global_options['auth']
    if url:
        try:
            u=urllib.request.urlopen(url,timeout=1)
            return True
        except urllib.error.URLError as e:
            #print (e.reason)
            if hasattr(e, 'code'):
                if e.code < 500:
                    return True
            return False
    else:
        return True

def meta_add(mlist,key,value):
    mlist.append("--header=X-Object-Meta-%s:%s" % (key, value))
    return mlist

# define minimum parser object to allow swiftstack shell to run (taken from swbundler)
def shell_minimal_options():

   parser = optparse.OptionParser()

   parser.add_option('-A', '--auth', dest='auth', default=_default_global_options['auth'])
   parser.add_option('-V', '--auth-version', default=_default_global_options['auth_version'])
   parser.add_option('-U', '--user', dest='user', default=_default_global_options['user'])
   parser.add_option('-K', '--key', dest='key', default=_default_global_options['key'])

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
   
   parser.add_option('-v', '--verbose', action='count', dest='verbose',
       default=1, help='Print more info.')
       
   # new mandatory bogosity required for swiftclient >= 3.0.0
   parser.add_option('--debug')
   parser.add_option('--info')

   return parser

# wrapper function for swiftstack shell functions
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

def sw_delete(*args):
    sw_shell(shell.st_delete,*args)

def sw_post(*args):
    sw_shell(shell.st_post,*args)
    

if __name__=="__main__":
    try:
        #tests()
        print ("to test, run this in a python shell:\n")
        print ("import fhswift")
        print ("fhswift.tests()") 
    except KeyboardInterrupt:
        print ('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
