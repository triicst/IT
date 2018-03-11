#!/usr/bin/env python3
import time
import os
import sys
import string

selections = {}
selections["campus - public cores"] = "gizmo_campus_public_cores"
selections["all - entire cluster"] = "gizmo_entire_cluster_cores"
selections["full - public nodes"] = "gizmo_full_public_cores"
selections["grabnode - public nodes"] = "gizmo_grabnode_public_cores"
selections["largenode - public cores"] = "gizmo_largenode_public_cores"
selections["private nodes"] = "gizmo_private_cores"

cmd = "/app/bin/hitparade --csv"

"""
label,cores_total,cores_pending,cores_idle,cores_used_restart,cores_used_priority,unix_load
campus - public cores,1280,265,564,0,716,870
all - entire cluster,2584,598,766,416,1402,1840
full - public nodes,304,0,174,0,130,26
grabnode - public nodes,0,0,0,0,0,0
largenode - public cores,84,0,0,0,84,31
private nodes,916,0,28,416,472,909
"""


lines = os.popen(cmd).readlines()
(total, pending, idle, used_restart, used_priority, load) = ("","","","","","")

for selection in selections.keys():
    for line in lines:
        if line.startswith(selection):
            inline = line.strip().split(",")
            total = inline[1]
            pending = inline[2]
            idle = inline[3]
            used_restart = inline[4]
            used_priority = inline[5]
            load = inline[6]
          
            if not selection.startswith("campus"): continue
            
            print("# TYPE %s_total gauge" % selections[selection])              
            print("%s_total %s" %  (selections[selection], total))

            print("# TYPE %s_pending gauge" % selections[selection])              
            print("%s_pending %s" %  (selections[selection], pending))

            print("# TYPE %s_idle gauge" % selections[selection])              
            print("%s_idle %s" %  (selections[selection], idle))

            print("# TYPE %s_used_restart gauge" % selections[selection])              
            print("%s_used_restart %s" %  (selections[selection], used_restart))

            print("# TYPE %s_used_priority gauge" % selections[selection])              
            print("%s_used_priority %s" %  (selections[selection], used_priority))

            print("# TYPE %s_load gauge" % selections[selection])              
            print("%s_load %s" %  (selections[selection], load))
