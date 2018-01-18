#!/bin/bash
/opt/node_exporter/scripts/gather_heavy_cpu_user.py > /opt/node_exporter/metrics_dump/heavy_cpu_user.prom.$$
mv /opt/node_exporter/metrics_dump/heavy_cpu_user.prom.$$ /opt/node_exporter/metrics_dump/heavy_cpu_user.prom
