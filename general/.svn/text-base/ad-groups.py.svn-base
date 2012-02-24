#!/usr/bin/env python

import sys,getopt,commands,os,ldap,ldap.sasl,grp
from ldap.controls import SimplePagedResultsControl

default_page_size=500

# split LDAP-returned strings into components while editing out '\'s
def skip_split(s,split_char=',',skip_char='\\'):
   split=[]
   partial=""
   skip=0

   for c in s:
      if skip==1:
         partial+=c
         skip=0
      elif c==skip_char:
         skip=1
      elif c==split_char:
         split.append(partial)
         partial=""
      else:
         partial+=c

   # append residual partial if it exists
   if partial!="":
      split.append(partial)

   return split

# open connection to LDAP server, assuming paging necessary to complete 
# retrieval
def open_ldap(url,base,search_flt,page_size=default_page_size):
   ldap.set_option(ldap.OPT_REFERRALS, 0)
   l = ldap.initialize(url)
   l.protocol_version = 3

   sasl_auth=ldap.sasl.sasl({},'GSSAPI')
   try:
      l.sasl_interactive_bind_s('',sasl_auth)
   except ldap.LOCAL_ERROR:
      print "Error: missing credential - Please run kinit"
      sys.exit()

   lc = SimplePagedResultsControl(
      ldap.LDAP_CONTROL_PAGE_OID,True,(page_size,'')
   )

   # Send search request
   msgid = l.search_ext(
     base,
     ldap.SCOPE_SUBTREE,
     search_flt,
     serverctrls=[lc]
   )

   return l,lc,msgid

# encapsulates LDAP paging mechanism, returning 0 if no more pages 
def ldap_paging(serverctrls,lc,l,base,search_flt,page_size=default_page_size):
   pctrls = [
      c
      for c in serverctrls
      if c.controlType == ldap.LDAP_CONTROL_PAGE_OID
   ]

   if pctrls:
      est, cookie = pctrls[0].controlValue
      if cookie:
         lc.controlValue = (page_size, cookie)
         msgid = l.search_ext(base, ldap.SCOPE_SUBTREE, search_flt,
                              serverctrls=[lc])
      else:
         return 0
   else:
      print "Warning: Server ignores RFC 2696 control."
      return 0

   return msgid

# generator encapulating paged ldap retrieval
def generate_ldap(url,base,search_flt,debug=0):
   l,lc,msgid=open_ldap(url,base,search_flt)

   pages = 0
   while True:
      pages += 1
      if debug:
         print "Getting page %d" % (pages,)
      rtype, rdata, rmsgid, serverctrls = l.result3(msgid)
      #print rdata
      for index,item in enumerate(rdata):
         #print index,type(item)
         for crud in list(item):
            #print type(crud),crud
            if isinstance(crud,dict):
               yield crud

      if debug:
         print '%d results' % len(rdata)
         break

      msgid=ldap_paging(serverctrls,lc,l,base,search_flt)
      if msgid==0:
         break 

def cn_members(member_list):
   return [x[3:] for name in member_list 
      for x in skip_split(name) if x[:3].lower()=="cn="]

def generate_pmembers(gmembers,diff):
   for gmember in gmembers:
      if diff:
         try:
            if grp.getgrnam(gmember):
               continue
         except KeyError:
            yield gmember
      else:
         yield gmember

def usage():
   print "fhgroups [options] [username]"
   print "Options:"
   print "\t-h : usage information"
   print "\t-c : count AD groups"
   print "\t-l : output as sorted line-per-entry list"
   print "\t-d : display AD groups not in local groups"
   print "\t-e : display AD groups also in ExcludedFromLDAPSync"
   print
   print "username : current user if not specified"

def main(argv):
   ldap_url = "ldap://dc.test.org"
   src_base = "dc=test,dc=org"

   count=0
   list=0
   diff=0

   xclude=0
   xgroups=[]
 
   try:
      opts,args=getopt.getopt(argv,"cldeh")
   except getopt.GetoptError:
      usage()
      sys.exit()

   for opt,arg in opts:
      if opt in ("-h"):
         usage()
         sys.exit()
      elif opt in ("-c"):
         count=1
      elif opt in ("-l"):
         list=1
      elif opt in ("-d"):
         diff=1
      elif opt in ("-e"):
         group_flt = r'(&(objectClass=group)(name=ExcludedFromLDAPSync))'
         for crud in generate_ldap(ldap_url,src_base,group_flt):
            xgroups=cn_members(crud['member'])
         xclude=1

   if not args:
      args=[os.getlogin()]

   if len(args)!=1 or '?' in args[0] or '*' in args[0]:
      usage()
   else:
      if list==0:
         print args[0]+":",

      user_flt=r'(&(objectcategory=person)(objectclass=user)(sAMAccountName=%s))' % (args[0])
      for crud in generate_ldap(ldap_url,src_base,user_flt):
         if 'memberOf' in crud:
            gmembers=cn_members(crud['memberOf'])
            if list==1:
               for pmember in generate_pmembers(sorted(gmembers),diff):
                   if xclude==0 or pmember in xgroups:
                      print pmember
            else:
               for pmember in generate_pmembers(gmembers,diff):
                   if xclude==0 or pmember in xgroups:
                      print pmember,

      if list==0:
         print

      if count:
         print "total",len(gmembers),"AD groups"

if __name__=="__main__":
   main(sys.argv[1:])
