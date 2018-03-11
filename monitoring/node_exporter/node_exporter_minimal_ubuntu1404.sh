#!/bin/bash
set -e

wget -q https://github.com/prometheus/node_exporter/releases/download/v0.15.1/node_exporter-0.15.1.linux-amd64.tar.gz
tar xf node_exporter-0.15.1.linux-amd64.tar.gz

if [ ! -d /opt/node_exporter ]; then
  mkdir /opt/node_exporter
fi

cp node_exporter-0.15.1.linux-amd64/node_exporter /opt/node_exporter/node_exporter

cat > /etc/init/node_exporter.conf << EOL
# Run node_exporter

start on startup

script
   /opt/node_exporter/node_exporter  --no-collector.arp \
        --no-collector.bcache \
        --no-collector.conntrack \
        --no-collector.entropy \
        --no-collector.edac \
        --no-collector.filefd \
        --no-collector.hwmon \
        --no-collector.infiniband \
        --no-collector.ipvs \
        --no-collector.mdadm \
        --no-collector.netstat \
        --no-collector.sockstat \
        --no-collector.stat \
        --no-collector.textfile \
        --no-collector.time \
        --no-collector.timex \
        --no-collector.uname \
        --no-collector.vmstat \
        --no-collector.wifi \
        --no-collector.xfs \
        --no-collector.zfs \
        --no-collector.mountstats \
        --collector.filesystem \
        --collector.cpu \
        --collector.diskstats \
        --collector.meminfo \
        --collector.loadavg \
        --collector.netdev
 
end script
EOL

service node_exporter start

rm -f node_exporter-0.15.1.linux-amd64.tar.gz
rm -rf node_exporter-0.15.1.linux-amd64

