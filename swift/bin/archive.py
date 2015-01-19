#!/usr/bin/env python3

import os,sys,getopt,tarfile

import swiftclient

import subprocess

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

def upload_file_to_swift(filename,swiftname,container,swift_conn):
   with open(filename,'rb') as localfile:
      swift_conn.put_object(container,swiftname,localfile)

def archive_tar_file(src_path,file_list,container,swift_conn):
   global tar_suffix

   # archive_name is name for archived object
   archive_name=src_path+tar_suffix
   # temp_archive_name is name of local tar file
   temp_archive_name=str(os.getpid())+os.path.basename(archive_name)
  
   # Create local tar file 
   create_tar_file(temp_archive_name,src_path,file_list)

   # Upload tar file to container as 'archive_name' using swift_conn
   upload_file_to_swift(temp_archive_name,archive_name,container,swift_conn)

   # Delete local tar file
   os.unlink(temp_archive_name)

# walk directory from current
def archive_to_swift(local_dir,container,swift_conn,no_hidden):
   for dir_name, subdir_list, file_list in os.walk(local_dir):
      rel_path=os.path.relpath(dir_name)
      if (not (no_hidden and is_hidden_dir(rel_path)) and file_list):
         archive_tar_file(dir_name,file_list,container,swift_conn)

# parse name into directory tree
def create_local_path(local_dir,archive_name):
   global tar_suffix

   path=os.path.join(local_dir,archive_name)
   if path.endswith(tar_suffix):
      path=path[:-len(tar_suffix)]

   os.makedirs(path)
   
   return path

def extract_to_local(local_dir,container,swift_conn,no_hidden):
   global tar_suffix

   try: 
      headers,objs=swift_conn.get_container(container)
      for obj in objs:
         if obj['name'].endswith(tar_suffix):
            if no_hidden and is_hidden_dir(obj['name']):
               continue

            term_path=create_local_path(local_dir,obj['name'])

            # download tar file and extract into terminal directory
            temp_file=str(os.getpid())+tar_suffix            
            subprocess.call(["swift","download",
               "--output="+temp_file,
               container,obj['name']])

            with tarfile.open(temp_file,"r:gz") as tar:
               tar.extractall(path=term_path)

            os.unlink(temp_file)
   except swiftclient.exceptions.ClientException:
      print("Error: cannot access Swift container '%s'!" % container)

def usage():
   print("archive [parameters]")
   print("Parameters:")
   print("\t-l local_directory (default .)")
   print("\t-c container (required)")
   print("\t-n (no hidden directories)")
   print("\t-x (extract from container to local directory)")

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
      swift_auth=os.environ.get("ST_AUTH")
      swift_user=os.environ.get("ST_USER")
      swift_key=os.environ.get("ST_KEY")

      if swift_auth and swift_user and swift_key:    
         swift_conn=swiftclient.Connection(authurl=swift_auth,
            user=swift_user,key=swift_key)

         if swift_conn:
            if extract:
               extract_to_local(local_dir,container,swift_conn,no_hidden)
            else:
               swift_conn.put_container(container)
               archive_to_swift(local_dir,container,swift_conn,no_hidden)

            swift_conn.close()
      else:
         print("Error: Missing Swift account information in environment!")

if __name__=="__main__":
   main(sys.argv[1:])
