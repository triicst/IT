#!/usr/bin/env python3
import os
import sys

"""
JOBID;NAME;PARTITION;ST;NODES;CPUS;ACCOUNT;USER;NODELIST
58456963;Extract;campus;PD;1;4;warren_h;dcoffey;
58456964;Extract;campus;PD;1;4;warren_h;dcoffey;
58456965;Extract;campus;PD;1;4;warren_h;dcoffey;
"""

def main():
    jobs = [l.strip() for l in os.popen(cmd).readlines()]
    large_states = {}
    campus_states = {}
    restart_states = {}
    owner_cores = {}
    state = ""
    for job in jobs:
        if job.startswith('CLUSTER'): continue
        j = job.split(';')
        partition = j[2].lower()
        if not partition in ['largenode', 'campus', 'restart']:
            continue
        state = state_name(j[3].upper())
        nodes = int(j[4])
        cpus = int(j[5])
        owner = j[6].lower()
        user = j[7].lower()

        if 'campus' in partition:
            campus_states[state] = campus_states.setdefault(state, 0) + 1
        if 'largenode' in partition:
            large_states[state] = large_states.setdefault(state, 0) + 1
        if 'restart' in partition:
            restart_states[state] = restart_states.setdefault(state, 0) + 1
        
        # only care about campus partition for owner core count
        if state == 'running' and 'campus' in partition:
            if 'campus' in partition:
                owner_cores[owner] = owner_cores.setdefault(owner, 0) + cpus 

    mtype = "# TYPE hpc_%s_jobstate_%s gauge"
    metric = "hpc_%s_jobstate_%s{partition=\"%s\"} %d"
    states = set()
    states.update(large_states.keys(), campus_states.keys(), restart_states.keys())
    for s in states:
        print(mtype % (cluster, s))
    for k in campus_states:
        print(metric % (cluster, k, "campus", campus_states[k]))
    for k in large_states:
        print(metric % (cluster, k, "largenode", large_states[k]))
    for k in restart_states:
        print(metric % (cluster, k, "restart", restart_states[k]))


    if state == "running":

        mtype = "# TYPE hpc_%s_ownercores gauge"
        metric = "hpc_%s_ownercores{owner=\"%s\"} %d"
        print(mtype % (cluster))
        for k in owner_cores:
            print(metric % (cluster, k, owner_cores[k]))


def state_name(state):
    st = {}
    st['PD'] = "pending"
    st['R'] = "running"
    st['CA'] = "cancelled"
    st['CF'] = "configuring"
    st['CG'] = "completing"
    st['CD'] = "completed"
    st['F'] = "failed"
    st['TO'] = "timeout"
    st['NF'] = "nodefailure"
    st['RV'] = "revoked"
    st['SE'] = "specialexit"
    
    return(st[state])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: cluster name required as command argument: beagle or gizmo accepted")
        sys.exit(1)
    elif sys.argv[1].lower() == "beagle":
        cmd = "/usr/bin/squeue --format=\"%i;%j;%P;%t;%D;%C;%a;%u;%N\" --noheader -M beagle"
    elif sys.argv[1].lower() == "gizmo":
        cmd = "/usr/bin/squeue --format=\"%i;%j;%P;%t;%D;%C;%a;%u;%N\" --noheader"
    else:
        print("Error: cluster name required as command argument: beagle or gizmo accepted")
        sys.exit(1)
    cluster = sys.argv[1].lower()
    main()
