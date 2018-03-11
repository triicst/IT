#!/bin/bash
source /app/Lmod/lmod/lmod/init/profile
export MODULEPATH=/app/easybuild/modules/all
ml Python/3.6.3-foss-2016b-fh1
/opt/node_exporter/scripts/gather_gizmo_cores.py > /opt/node_exporter/metrics_dump/gizmo_metrics.prom.$$
mv /opt/node_exporter/metrics_dump/gizmo_metrics.prom.$$ /opt/node_exporter/metrics_dump/gizmo_metrics.prom
