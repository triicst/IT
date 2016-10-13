LF Backup
==

LF Backup stands for large file backup. The script has the following features:

* take a file list from a csv file or an SQL table and backup each file 
  to object storage (e.g. swift) 

* if the file has an atime within the last x days (configurable) take an md5sum
  of that file and store the md5sum in an attribute / meta data called md5sum  

* check if the file is already in object store and do not upload if the file size and mtime is identical 

* notify a list of email-addresses after finishing. attach list of files that were uploaded. create one 
  file list per file owner (hutchnet-id)

* log every file that was uploaded to syslog, detailed logging of success and failure to enable storage team to monitor success / failure via splunk 

* bash script lf-backup is a wrapper for python script lf-backup.py, lf-backup sources and sets env vars 
  with credentials and lf-backup.py only reads environments vars

* main script lf-backup.py only uses swift functions via  new swift serives api http://docs.openstack.org/developer/python-swiftclient/service-api.html (e.g. https://github.com/FredHutch/swiftclient-gui/blob/master/SwiftClientGUI.py#L194 ) or via lagacy functions in lflib.py. The goal is to keep the main script lf-backup.py as clean as possible so it cna be easily modified by the storage team. 
  
* test.csv contains some data pointers

* segment size should be 1GB, segment container name should be .segments-containername, object type
  is slo, not dlo

* backup with full path but replace prefix, for example a file /fh/fast/lastname_f/project/file.bam would be 
  copied to container/bucket bam-backup in account Swift__ADM_IT_backup. The target path would be 
  /bam-bucket/lastname_f/project/file.bam ..... we would need a command option such as --srcroot or --prefix or
  something like that, e.g. --prefix=/fh/fast


