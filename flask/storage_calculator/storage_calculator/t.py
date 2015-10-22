#! /usr/bin/env python

from authentication import LDAPAuth


ldap_ad = LDAPAuth('phsldap', 'Trop1calW1nter', domain='fhcrc.org',
        base_dn='dc=fhcrc,dc=org', ldap_url='ldap://dc.fhcrc.org')

print ldap_ad.authenticate()

