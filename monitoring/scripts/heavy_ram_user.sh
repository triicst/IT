#!/bin/bash
/opt/node_exporter/scripts/gather_heavy_ram_user.py > /opt/node_exporter/metrics_dump/heavy_ram_user.prom.$$
mv /opt/node_exporter/metrics_dump/heavy_ram_user.prom.$$ /opt/node_exporter/metrics_dump/heavy_ram_user.prom
