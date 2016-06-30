#!/bin/bash

# Variables 
db1=dev-db1
db2=dev-db2
db3=dev-db3
userAdminPasswd=P@assword
rootAdminPasswd=P@assword
oncoscapePasswd=P@assword
oncoscapeReadPasswd=P@assword

# Generate an SSH key
/usr/bin/ssh-keygen -f /root/.ssh/id_rsa -t rsa -N ''

# Copy SSH keys to other nodes
scp -o "StrictHostKeyChecking no" /root/.ssh/id_rsa.pub root@${db2}:/root/.ssh/authorized_keys
scp -o "StrictHostKeyChecking no" /root/.ssh/id_rsa.pub root@${db3}:/root/.ssh/authorized_keys

cat > /root/bootstrap-base.sh << EOL
#!/bin/bash

# Format and mount data volume 
mkfs -t ext4 /dev/xvdf
mkdir /data
mount /dev/xvdf /data 
echo "/dev/xvdf       /data   ext4    defaults,nofail,nobootwait        0 2"  >> /etc/fstab

# Create and activate SWAP space
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile   none    swap    sw    0   0"  >> /etc/fstab

# Install Docker
apt-get -y update
apt-get -y install apt-transport-https ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" > /etc/apt/sources.list.d/docker.list
apt-get -y update
apt-get -y purge lxc-docker
apt-get -y install linux-image-extra-\$(uname -r)
apt-get -y install docker-engine

# Pull down the latest stable release of MongoDB (3.2.7 at this time)
docker pull mongo:3.2.7
EOL

# Run bootstrap script on DB1
chmod 755 /root/bootstrap-base.sh
/root/bootstrap-base.sh

# Run bootstrap script on DB2
scp /root/bootstrap-base.sh root@${db2}:/root/bootstrap-base.sh 
ssh root@${db2} /root/bootstrap-base.sh

# Run bootstrap script on DB3
scp bootstrap-base.sh root@${db3}:/root/bootstrap-base.sh 
ssh root@${db3} /root/bootstrap-base.sh


# Disable transparent hugepages
cat > /etc/init.d/disable-transparent-hugepages.sh << EOL
#!/bin/bash
### BEGIN INIT INFO
# Provides:          disable-transparent-hugepages
# Required-Start:    \$local_fs
# Required-Stop:
# X-Start-Before:    mongod mongodb-mms-automation-agent
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Disable Linux transparent huge pages
# Description:       Disable Linux transparent huge pages, to improve
#                    database performance.
### END INIT INFO

case \$1 in
  start)
    if [ -d /sys/kernel/mm/transparent_hugepage ]; then
      thp_path=/sys/kernel/mm/transparent_hugepage
    elif [ -d /sys/kernel/mm/redhat_transparent_hugepage ]; then
      thp_path=/sys/kernel/mm/redhat_transparent_hugepage
    else
      return 0
    fi

    echo 'never' > \${thp_path}/enabled
    echo 'never' > \${thp_path}/defrag

    unset thp_path
    ;;
esac
EOL

# Disable transparent hugepages on DB1
chmod 755 /etc/init.d/disable-transparent-hugepages.sh
update-rc.d disable-transparent-hugepages.sh defaults
/etc/init.d/disable-transparent-hugepages.sh start

# Disable transparent hugepages on DB2
scp /etc/init.d/disable-transparent-hugepages.sh root@${db2}:/etc/init.d/disable-transparent-hugepages.sh 
ssh root@${db2} update-rc.d disable-transparent-hugepages.sh defaults
ssh root@${db2} /etc/init.d/disable-transparent-hugepages.sh start

# Disable transparent hugepages on DB3
scp /etc/init.d/disable-transparent-hugepages.sh root@${db3}:/etc/init.d/disable-transparent-hugepages.sh
ssh root@${db3} update-rc.d disable-transparent-hugepages.sh defaults
ssh root@${db3} /etc/init.d/disable-transparent-hugepages.sh start

# Setup MongoDB data folders
mkdir /data/keys
mkdir /data/db
mkdir /data/setup

# Change ownership to mongo user (UID is for inside container not host OS)
chown 999 /data/keys
chown 999 /data/db
chown 999 /data/setup

# Generate shared mongo cluster key
openssl rand -base64 741 > /data/keys/mongodb-keyfile
chmod 600 /data/keys/mongodb-keyfile
chown 999 /data/keys/mongodb-keyfile


# Createusers.js script (only needs to be run on first node)
cat > /data/setup/createusers.js << EOL
conn = new Mongo("localhost:27017");
db = conn.getDB("admin")

db.createUser( {
     user: "userAdmin",
     pwd: "${userAdminPasswd}",
     roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
   });

db.createUser( {
     user: "rootAdmin",
     pwd: "${rootAdminPasswd}",
     roles: [ { role: "root", db: "admin" } ]
   });

db.createUser( {
     user: "oncoscape",
     pwd: "${oncoscapePasswd}",
     roles: [ { role: "readWriteAnyDatabase", db: "admin" } ]
   });

db.createUser( {
     user: "oncoscapeRead",
     pwd: "${oncoscapeReadPasswd}",
     roles: [ { role: "readAnyDatabase", db: "admin" } ]
   });
EOL
chown 999 /data/setup/createusers.js


# Create rs-inti.js script
cat > /data/setup/rs-init.js << EOL
conn = new Mongo("localhost:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "${rootAdminPasswd}");
rs.initiate();
EOL
chown 999 /data/setup/rs-init.js

# Create add-nodes.js script 
cat > /data/setup/add-nodes.js  << EOL
conn = new Mongo("localhost:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "${rootAdminPasswd}");
rs.add("${db2}");
rs.add("${db3}");
cfg = rs.conf()
cfg.members[0].priority = 1
cfg.members[1].priority = 0.5
cfg.members[2].priority = 0.5
rs.reconfig(cfg)
EOL
chown 999 /data/setup/add-nodes.js

# Create enable readscript to run on DB2 and DB3 
cat > /data/setup/enable-reads-on-secondary.js << EOL
conn = new Mongo("localhost:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "${rootAdminPasswd}");
rs.slaveOk();
EOL
chown 999 /data/setup/enable-reads-on-secondary.js

# Copy key and scripts to DB2 and DB3 
rsync -ave ssh /data/ root@${db2}:/data/
rsync -ave ssh /data/ root@${db3}:/data/

# Start a mongo container without auth enabled on DB1
docker run --name mongodb \
-v /data/db:/data/db \
-v /data/keys:/opt/keyfile \
-v /data/setup:/setup \
--hostname="${db1}" \
-p 27017:27017 -p 27018:27018 -p 27019:27019 -p 28017:28017 \
-d mongo:3.2.7 --smallfiles

# Create mongo users on DB1 
sleep 10 
docker exec -ti mongodb mongo /setup/createusers.js

# Stop and delete the mongodb container and recreate it with authentication and a replicaset enabled
docker stop mongodb
docker rm mongodb
sleep 10
docker run --name mongodb \
-v /data/db:/data/db \
-v /data/keys:/opt/keyfile \
-v /data/setup:/setup \
--restart always \
--hostname="${db1}" \
-p 27017:27017 -p 27018:27018 -p 27019:27019 -p 28017:28017 \
-d mongo:3.2.7 --auth --smallfiles \
--keyFile /opt/keyfile/mongodb-keyfile \
--replSet "rs0"

# Run script to initiate replicaset
sleep 10 
docker exec -ti mongodb mongo /setup/rs-init.js

# Start mongo on DB2
ssh root@${db2} docker run --name mongodb \
-v /data/db:/data/db \
-v /data/keys:/opt/keyfile \
-v /data/setup:/setup \
--restart always \
--hostname="${db2}" \
-p 27017:27017 -p 27018:27018 -p 27019:27019 -p 28017:28017 \
-d mongo:3.2.7 --auth --smallfiles \
--keyFile /opt/keyfile/mongodb-keyfile \
--replSet "rs0"

# Start mongo on DB3
ssh root@${db3} docker run --name mongodb \
-v /data/db:/data/db \
-v /data/keys:/opt/keyfile \
-v /data/setup:/setup \
--restart always \
--hostname="${db3}" \
-p 27017:27017 -p 27018:27018 -p 27019:27019 -p 28017 \
-d mongo:3.2.7 --auth --smallfiles \
--keyFile /opt/keyfile/mongodb-keyfile \
--replSet "rs0"

# Add DB2 and DB3 to the cluster and prefer DB1 as the primary node
sleep 10
docker exec -ti mongodb mongo /setup/add-nodes.js

# Enable DB2 and DB3 secondaries to serve reads
sleep 10
ssh root@${db2} docker exec mongodb mongo /setup/enable-reads-on-secondary.js
ssh root@${db3} docker exec mongodb mongo /setup/enable-reads-on-secondary.js

# Done! the cluster should be ready to use 
