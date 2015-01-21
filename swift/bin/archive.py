#!/usr/bin/env python3

import os,sys,getopt,tarfile
import getpass

import socket
import optparse

from swiftclient import Connection

from swiftclient import shell
from swiftclient import RequestException
from swiftclient.exceptions import ClientException
from swiftclient.multithreading import OutputManager

# define minimum parser object to allow swiftstack shell to run 
def shell_minimal_options():
   parser = optparse.OptionParser()

   parser.add_option('-A', '--auth', dest='auth',
      default=os.environ.get('ST_AUTH'))
   parser.add_option('-V', '--auth-version',
      default=os.environ.get('ST_AUTH_VERSION',
         (os.environ.get('OS_AUTH_VERSION','1.0'))))
   parser.add_option('-U', '--user', dest='user',
      default=os.environ.get('ST_USER'))
   parser.add_option('-K', '--key', dest='key',
      default=os.environ.get('ST_KEY'))
 
   parser.add_option('--os_user_id')
   parser.add_option('--os_user_domain_id')
   parser.add_option('--os_user_domain_name')
   parser.add_option('--os_tenant_id')
   parser.add_option('--os_tenant_name')
   parser.add_option('--os_project_id')
   parser.add_option('--os_project_domain_id')
   parser.add_option('--os_project_name')
   parser.add_option('--os_project_domain_name')
   parser.add_option('--os_service_type')
   parser.add_option('--os_endpoint_type')
   parser.add_option('--os_auth_token')
   parser.add_option('--os_storage_url')
   parser.add_option('--os_region_name')
   
   parser.add_option('-v', '--verbose', action='count', dest='verbose',
       default=1, help='Print more info.')

   return parser

# wrapper function for swiftstack shell functions
def sw_shell(sw_fun,*args):
   args = ('',) + args
   with OutputManager() as output:
      parser = shell_minimal_options()
      try:
         sw_fun(parser, list(args), output)
      except (ClientException, RequestException, socket.error) as err:
         output.error(str(err))
 
def sw_stat(*args):
   sw_shell(shell.st_stat,*args)

def sw_ls(*args):
   sw_shell(shell.st_list,*args)
 
def sw_download(*args):
   sw_shell(shell.st_download,*args)
 
def sw_upload(*args):
   sw_shell(shell.st_upload,*args)
 
def sw_post(*args):
   sw_shell(shell.st_post,*args)
 
# suffix of archive files
tar_suffix=".tar.gz"

# True if 1st char of path member is '.' else False
def is_hidden_dir(dir_name):
   for item in dir_name.split('/'):
      if item[0]=='.':
         return True

   return False

def create_tar_file(filename,src_path,file_list):
   with tarfile.open(filename,"w:gz") as tar:
      for file in file_list:
         tar.add(os.path.join(src_path,file),file)

def upload_file_to_swift(filename,swiftname,container):
   sw_upload("--object-name="+swiftname,
      "--segment-size=2147483648",
      "--use-slo",
      "--segment-container=.segments_testing",
      "--header=X-Object-Meta-Uploaded-by:"+getpass.getuser(),
      container,filename)

def archive_tar_file(src_path,file_list,container):
   global tar_suffix

   # archive_name is name for archived object
   archive_name=src_path+tar_suffix
   # temp_archive_name is name of local tar file
   temp_archive_name=str(os.getpid())+os.path.basename(archive_name)
  
   # Create local tar file 
   create_tar_file(temp_archive_name,src_path,file_list)

   # Upload tar file to container as 'archive_name' 
   upload_file_to_swift(temp_archive_name,archive_name,container)

   # Delete local tar file
   os.unlink(temp_archive_name)

# walk directory from current
def archive_to_swift(local_dir,container,no_hidden):
   for dir_name, subdir_list, file_list in os.walk(local_dir):
      rel_path=os.path.relpath(dir_name)
      if (not (no_hidden and is_hidden_dir(rel_path)) and file_list):
         archive_tar_file(dir_name,file_list,container)

# parse name into directory tree
def create_local_path(local_dir,archive_name):
   global tar_suffix

   path=os.path.join(local_dir,archive_name)
   if path.endswith(tar_suffix):
      path=path[:-len(tar_suffix)]

   if not os.path.exists(path):
      os.makedirs(path)
   
   return path

def create_sw_conn():
   swift_auth=os.environ.get("ST_AUTH")
   swift_user=os.environ.get("ST_USER")
   swift_key=os.environ.get("ST_KEY")

   if swift_auth and swift_user and swift_key:
      return Connection(authurl=swift_auth,user=swift_user,key=swift_key)

   print("Error: Swift environment not configured!")

def extract_to_local(local_dir,container,no_hidden):
   global tar_suffix

   swift_conn=create_sw_conn()
   if swift_conn:
      try: 
         headers,objs=swift_conn.get_container(container)
         for obj in objs:
            if obj['name'].endswith(tar_suffix):
               if no_hidden and is_hidden_dir(obj['name']):
                  continue

               term_path=create_local_path(local_dir,obj['name'])

               # download tar file and extract into terminal directory
               temp_file=str(os.getpid())+tar_suffix
               sw_download("--output="+temp_file,container,obj['name'])

               with tarfile.open(temp_file,"r:gz") as tar:
                  tar.extractall(path=term_path)

               os.unlink(temp_file)
      except ClientException:
         print("Error: cannot access Swift container '%s'!" % container)

      swift_conn.close()

def usage():
   print("archive [parameters]")
   print("Parameters:")
   print("\t-l local_directory (default .)")
   print("\t-c container (required)")
   print("\t-x (extract from container to local directory)")
   print("\t-n (no hidden directories)")

def validate_dir(path,param):
   if not os.path.isdir(path):
      print("Error: %s '%s' is not accessible!" % (param,path))
      sys.exit()

   return(path)

# Fix now unneeded dest param
def main(argv):
   local_dir="."
   # default container is invalid
   container=""
   extract=False
   no_hidden=False

   try:
      opts,args=getopt.getopt(argv,"l:c:xnh")
   except getopt.GetoptError:
      usage()
      sys.exit()

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-l"): # override default local directory
         local_dir=validate_dir(arg,"local")
      elif opt in ("-c"): # set container
         container=arg
      elif opt in ("-x"): # extract mode
         extract=True
      elif opt in ("-n"): # set no-hidden flag to skip .*
         no_hidden=True

   if not container:
      usage()
   else:
      if extract:
         extract_to_local(local_dir,container,no_hidden)
      else:
         sw_post(container)
         archive_to_swift(local_dir,container,no_hidden)

if __name__=="__main__":
   main(sys.argv[1:])
