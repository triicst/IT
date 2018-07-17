#!/usr/bin/env python3
import os
import sys
import time

cmd = "/usr/bin/ldapsearch -x -LLL -H ldap://%s -b 'ou=group,dc=local' '(&(objectClass=posixGroup)(memberUid=mrg))' cn"
metric = "ldap_response_time_ms"
header = "# TYPE %s gauge" % metric
output = "%s{server=\"%s\"} %s"
expect = "cn=_ADM_SciComp_grp,ou=group,dc=local"

def main(servers):
    print(header)
    for server in servers:
        try:
            start = time.time()
            out = os.popen(cmd % server).read()
            stop = time.time()
            elapsed = round(float(stop - start) * 1000, 3)
            if expect in out:
                print(output % (metric, server, elapsed))
            else:
                print(output % (metric, server, "NaN"))
        except:
            print(output % (metric, server, "NaN"))

if __name__ == "__main__":
    servers = sys.argv[1:]
    main(servers)
