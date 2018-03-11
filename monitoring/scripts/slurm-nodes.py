#!/usr/bin/env python3
import os
import sys

"""
HOSTNAMES;CPUS;CPUS(A/I/O/T);MEMORY;FEATURES;CPU_LOAD;FREE_MEM;STATE
gizmoe19;16;0/0/16/16;1;bradley_p,br3norm,restart;N/A;N/A;down*
gizmoe6;16;16/0/0/16;64224;bradley_p,br3norm,restart;16.78;48387;alloc
gizmoe7;16;16/0/0/16;64224;bradley_p,br3norm,restart;16.02;47164;alloc
gizmoe8;16;16/0/0/16;64224;bradley_p,br3norm,restart;16.11;46803;alloc
gizmoe9;16;16/0/0/16;64224;bradley_p,br3norm,restart;15.67;46357;alloc
gizmoe10;16;16/0/0/16;64224;bradley_p,br3norm,restart;16.80;47858;alloc
"""


def main():
    nodes = [l.strip() for l in os.popen(cmd).readlines()]
    node_states = {}
    cores = 0
    cores_alloc = 0
    mem = 0
    mem_avail = 0
    load = 0
    for node in nodes:
        if node.startswith('CLUSTER'): continue
        n = node.split(';')
        state = n[7].lower().replace('mix', 'partial')
        features = n[4].lower()
        if not 'campus' in features and cluster == 'gizmo':
            continue
        if not "*" in state and not "down" in state and not "~" in state and not "drain" in state and not "fail" in state and not "#" in state:
            ncores = int(n[1])
            ncores_alloc = int(n[2].split('/')[0])
            nmem = int(n[3])
            nmem_free = int(n[6])
            cores += ncores
            cores_alloc += ncores_alloc
            mem += nmem
            mem_avail += nmem_free
            load += float(n[5])
            features = n[4]

        for char in "*~@#$":
            state = state.replace(char, '')

        node_states[state] = node_states.setdefault(state, 0) + 1

    mtype = "# TYPE hpc_%s_nodestate_%s gauge"
    metric = "hpc_%s_nodestate_%s %d"
    for k in node_states:
        print(mtype % (cluster, k))
        print(metric % (cluster, k, node_states[k]))
    
    print("# TYPE hpc_%s_cores_total gauge" % (cluster))
    print("hpc_%s_cores_total %d" % (cluster, cores))

    print("# TYPE hpc_%s_cores_used gauge" % (cluster))
    print("hpc_%s_cores_used %d" % (cluster, cores_alloc))

    print("# TYPE hpc_%s_mem_total gauge" % (cluster))
    print("hpc_%s_mem_total %d" % (cluster, mem))
    
    print("# TYPE hpc_%s_mem_used gauge" % (cluster))
    print("hpc_%s_mem_used %d" % (cluster, mem - mem_avail))

    print("# TYPE hpc_%s_load gauge" % (cluster))
    print("hpc_%s_load %0.2f" % (cluster, load))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: cluster name required as command argument: beagle or gizmo accepted")
        sys.exit(1)
    elif sys.argv[1].lower() == "beagle":
        cmd = "/usr/bin/sinfo --format=\"%n;%c;%C;%m;%f;%O;%e;%t\" --noheader -M beagle"
    elif sys.argv[1].lower() == "gizmo":
        cmd = "/usr/bin/sinfo --format=\"%n;%c;%C;%m;%f;%O;%e;%t\" --noheader"
    else:
        print("Error: cluster name required as command argument: beagle or gizmo accepted")
        sys.exit(1)
    cluster = sys.argv[1].lower()
    main()
