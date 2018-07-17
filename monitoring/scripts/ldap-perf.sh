#!/bin/bash
set -e
/opt/node_exporter/scripts/ldap-perf.py gizmo2.fhcrc.org ldap-j4-01-prd.fhcrc.org ldap-j4-02-prd.fhcrc.org > /opt/node_exporter/metrics_dump/ldap-perf.prom.$$ 2> /dev/null
mv /opt/node_exporter/metrics_dump/ldap-perf.prom.$$ /opt/node_exporter/metrics_dump/ldap-perf.prom
