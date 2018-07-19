#!/usr/bin/env python
import os
import sys

for content in sys.stdin:
    if str('Users of') == content[0:8]:
        words = content.split()
        feature = words[2][:-1]
        total = words[5]
        used = words[10]
        print("# TYPE matlab_%s_total gauge" % (feature.lower()))
        print("matlab_%s_total %s" % (feature.lower(), total))
        print("")
        print("# TYPE matlab_%s_used gauge" % (feature.lower()))
        print("matlab_%s_used %s" % (feature.lower(), used))
        print("")

        if int(used) > 0:
            ud = {}
            print("# TYPE matlab_%s_users gauge" % (feature.lower()))
            header = [next(sys.stdin) for x in xrange(4)]
            for content in sys.stdin:
                if len(content) < 4:
                    break
                user = content.split()[0].lower()
                if not user in ud:
                    ud[user] = 1   
                else:
                    ud[user] = ud[user] + 1
            for u in ud:
                print("matlab_%s_users{user=\"%s\"} %s" % (feature.lower(), u, ud[u]))
            print("")
