#!/usr/bin/env python2.7

# ldapsearch -LLL -x -W -D mrg@fhcrc.org -H ldap://dc.fhcrc.org:389 "(&(sAMAccountType=805306368)(|(title=Associate Member)(title=Full Member)))" -b "dc=fhcrc,dc=org"  title displayName sAMAccountName
#
# mprlic, HVTN Users, HVTN, VIDI, fhcrc.org
# dn: CN=mprlic,OU=HVTN Users,OU=HVTN,OU=VIDI,DC=fhcrc,DC=org
# title: Assistant Member
# displayName: Prlic, Martin
# directReports: CN=bseymour,OU=Users,OU=Accounts,OU=VIDI,DC=fhcrc,DC=org
# directReports: CN=Coffee\, Lane,OU=Users,OU=Accounts,OU=VIDI,DC=fhcrc,DC=org
# directReports: CN=tchu,OU=Users,OU=Accounts,OU=VIDI,DC=fhcrc,DC=org
# directReports: CN=Roepke\, Sarah A,OU=Users,OU=Accounts,OU=VIDI,DC=fhcrc,DC=org
#

# For each "Full" or "Associate" member:
    # create an account name "Last_First"
    # for each direct report:
        # create an idcfg.txt entry with
        # user:<username> alist=<account> adef=<account>

import sys
import ldap

# IDEntries[ 'joeu': ["adef", ['acct1', 'acct2']]]
IDEntries = {}
overrides = "overrides.txt"

BindDN, Secret = sys.argv[1:3]

ADServer = "ldap://dc.fhcrc.org"
ADSearchBase = "dc=fhcrc,dc=org"
ADSearchScope = ldap.SCOPE_SUBTREE

l = ldap.initialize( ADServer )
l.set_option(ldap.OPT_REFERRALS, 0)
l.simple_bind_s( BindDN, Secret )


MemberFilter = ( "(&(sAMAccountType=805306368)" +
                "(|(title=Assistant Member)(title=Associate Member)(title=Full Member)))"
               )
Attrs = [ "displayName", "directReports", "sAMAccountName" ]

r = l.search( ADSearchBase, ADSearchScope, MemberFilter, Attrs )

Type, Results = l.result( r, 60 )

for result in Results:
    if not result[0]:
        continue

    # Clean up display name- sometimes the title is included-
    # ['Houghton MD, A. McGarry']
    #   ^------^     ^
    #       |        |
    # split on spaces and use first letter found
    lname,fname = result[1]['displayName'][0].split( ', ' )
    lname = lname.split( " " )[0].lower()
    fname = fname.split( " " )[0].lower()

    actname = lname + "_" + fname[0]

    # Add the account owner to their own account
    # print result
    samname = result[1]['sAMAccountName'][0]
    adef = actname

    if samname in IDEntries.keys():
        IDEntries[ samname ].append( actname )
    else:
        IDEntries[ samname ] = [ actname ]

    if 'directReports' in result[1]:
        for dn in result[1][ 'directReports' ]:
            dn = dn.replace( '\\', '\\5c' )
            dn = dn.replace( '(', '\\28' )
            dn = dn.replace( ')', '\\29' )
            # print ">>> looking for " + dn

            filter = ( "(&(sAMAccountType=805306368)" +
                      "(distinguishedName=" + dn + "))"
                     )
            attrs = [ "sAMAccountName", ]

            q = l.search( ADSearchBase, ADSearchScope, filter, attrs )

            namesearch = l.result( q, 60 )[1]

            if namesearch[0][0]:
                samname = namesearch[0][1]['sAMAccountName'][0]

                if samname in IDEntries.keys():
                    IDEntries[ samname ].append( actname )
                else:
                    IDEntries[ samname ] = [ actname ]

#
# Now read in overrides & manual entries
#
# Overrides are lines of fields separated by spaces
# first field is the user, the rest are accounts that the
# user can access:
#  alice acct1 acct2 acct3 ...
#
f = open( overrides )
for line in f:
    t = line.split()
    if t[0] in IDEntries.keys():
        IDEntries[ t[0] ] = IDEntries[ t[0] ] + t[1:]
    else:
        IDEntries[ t[0] ] = t[1:]

    if t[1] == 'ALL':
        IDEntries[ t[0] ] = [ 'ALL' ]


for entry in IDEntries:
    # user:<username> alist=<account> adef=<account>
    print "user:{} alist={} adef={}".format(
        entry, ",".join( IDEntries[ entry ]), IDEntries[ entry ][0]
    )

