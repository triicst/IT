#!/bin/bash
set -e

if [ -z "$(getent passwd node_exporter)" ]; then
   useradd --no-create-home --shell /bin/false node_exporter
fi

wget -q https://github.com/prometheus/node_exporter/releases/download/v0.15.1/node_exporter-0.15.1.linux-amd64.tar.gz
tar xf node_exporter-0.15.1.linux-amd64.tar.gz

if [ ! -d /opt/node_exporter ]; then
  mkdir /opt/node_exporter
fi

if [ ! -d /opt/node_exporter/metrics_dump ]; then
  mkdir /opt/node_exporter/metrics_dump 
fi

cp node_exporter-0.15.1.linux-amd64/node_exporter /opt/node_exporter/node_exporter
chown node_exporter:node_exporter /opt/node_exporter/node_exporter

cat > /etc/systemd/system/node_exporter.service << EOL
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/opt/node_exporter/node_exporter  --no-collector.arp \
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
        --collector.netdev \
        --collector.textfile \
        --collector.textfile.directory /opt/node_exporter/metrics_dump


[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter
systemctl --no-pager status node_exporter

rm -f node_exporter-0.15.1.linux-amd64.tar.gz
rm -rf node_exporter-0.15.1.linux-amd64

