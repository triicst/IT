#!/bin/bash
set -e
/opt/node_exporter/scripts/slurm-nodes.py $1 > /opt/node_exporter/metrics_dump/slurm_${1}_nodes.prom.$$
mv /opt/node_exporter/metrics_dump/slurm_${1}_nodes.prom.$$ /opt/node_exporter/metrics_dump/slurm_${1}_nodes.prom
