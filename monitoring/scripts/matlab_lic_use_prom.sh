#!/bin/bash
/root/bin/lmstat -a | /root/bin/matlab_lic_use_prom.py > /opt/node_exporter/metrics_dump/matlab.prom.$$
mv /opt/node_exporter/metrics_dump/matlab.prom.$$ /opt/node_exporter/metrics_dump/matlab.prom
