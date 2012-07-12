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

class idcfg:
    """
    A class containing MWM identity manager entries

    IDEntries{
        'joeu': {
            username: 'joeu',
            default: 'adef',
            accounts: [ 'a1', 'a2', ... ]
        },
        'alice': {
            username: 'alice',
            default: 'adef',
            accounts: [ 'a1', 'a2', ... ]
        },
        ...
    }
    """
    def __init__( self ):
        """
        Intitialize the dictionary object that contains the entries

        """
        self.entries = {}

    def entryExists(self, username):
        """
        Check for the existence of an entry in the account lists

        Returns True if the entry is found, false if not.
        """
        if username in self.entries.keys():
            return True
        else:
            return False

    def insertEntry( self, username, adef=None, alist=[] ):
        """
        Creates a new entry in the list

        Minimally pass in the username.  Default and account
        list are empty unless passed in when called

        Will raise an exception if the entry already exists
        """

        if self.entryExists( username ):
            raise KeyError(
                'Insert into existing entry ' + username
            ) 
            return False
        self.entries[username] = {}
        self.entries[username]['username'] = username
        self.entries[username]['default'] = adef
        self.entries[username]['accounts'] = alist

    def getEntry( self, username ):
        """
        Return a single entry

        Returns an entry in the list- need to handle circumstances
        where the username doesn't exist
        """
        
        return self.entries[username]

    def setDefaultAccount( self, username, adef ):
        """
        Set the default account for the user

        Updates the default account for the user. Will raise
        LookupError exception if the entry doesn't exist
        """

        if not adef in self.entries[username]['accounts']:
            raise LookupError(
                'Account \'' + adef + '\' not in users account list'
            )
        self.entries[username]['default'] = adef

    def getKeys( self ):
        for entry in self.entries:
            print entry

    def getAllEntries( self ):
        """
        Returns generator for iterating through entries

        Returns a generator object for use in iterating through
        account entries
        """
        for entry in self.entries:
            yield self.entries[entry]

    def updateAccountList( self, username, alist ):
        """
        Updates the list of accounts

        Probably inaccurate.  Actually only adds accounts to
        the list of accounts for an entry.  Doesn't accommodate
        removal, etc.  Probably not important
        """
        self.entries[username]['accounts'] = (
            self.entries[username]['accounts'] + alist
        )



IDEntries = idcfg()

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
    samname = result[1]['sAMAccountName'][0]
    adef = actname

    try:
        IDEntries.insertEntry( samname, adef, [actname] )
    except KeyError:
        IDEntries.updateAccountList( samname, [actname] )
        IDEntries.setDefaultAccount( samname, adef )

    if 'directReports' in result[1]:
        for dn in result[1][ 'directReports' ]:
            dn = dn.replace( '\\', '\\5c' )
            dn = dn.replace( '(', '\\28' )
            dn = dn.replace( ')', '\\29' )

            filter = ( "(&(sAMAccountType=805306368)" +
                      "(distinguishedName=" + dn + "))"
                     )
            attrs = [ "sAMAccountName", ]

            q = l.search( ADSearchBase, ADSearchScope, filter, attrs )

            namesearch = l.result( q, 60 )[1]

            if namesearch[0][0]:
                samname = namesearch[0][1]['sAMAccountName'][0]

                if IDEntries.entryExists( samname ):
                    IDEntries.updateAccountList( samname, [actname] )
                else:
                    IDEntries.insertEntry( samname, "", [ actname ] )

#
# Now read in overrides & manual entries
#
# Overrides are lines of fields separated by spaces
# first field is the user, the rest are accounts that the
# user can access:
#  alice adef acct1 acct2 acct3 ...
#
f = open( overrides )
for line in f:
    t = line.split()
    if IDEntries.entryExists( t[0] ):
        IDEntries.updateAccountList( t[0], t[2:] )
        IDEntries.setDefaultAccount( t[0], t[1] )
    else:
        IDEntries.insertEntry( t[0], adef=t[1], alist=t[2:] )

for k in IDEntries.getAllEntries():
    if k['default'] == "":
        k['default'] = k['accounts'][0]

    print "user:{} alist={} adef={}".format(
        k['username'], ",".join( k['accounts'] ), k['default']
    )

