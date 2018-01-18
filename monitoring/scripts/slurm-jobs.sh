#!/bin/bash
set -e
/opt/node_exporter/scripts/slurm-jobs.py $1 > /opt/node_exporter/metrics_dump/slurm_${1}_jobs.prom.$$
mv /opt/node_exporter/metrics_dump/slurm_${1}_jobs.prom.$$ /opt/node_exporter/metrics_dump/slurm_${1}_jobs.prom
