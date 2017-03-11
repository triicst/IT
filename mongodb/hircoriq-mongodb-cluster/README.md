# HICORIQ MongoDB Install and Configuration Instructions

## Data Disk Setup [all nodes]

The MongoDB database files must be encrypted at rest, so you should already have an encrypted EBS volume added to each database server. This volume must be formated with the XFS filesystem and mounted at /data. The data volume should be configured to mount automatically via a entry in the /etc/fstab file like this:

```
/dev/xvdb              /data     xfs    defaults                0 2
```

Eash node in the replica cluster should have an XFS formated data volume mounted at /data and configured to mount at boot time before moving on to the next step. 


## Disable Transparent Hugepages [all nodes] 

MongoDB recomends that transparent hugepages are disabled in the linux kernel on each mongodb server to impore performance. Execute the following command to create the file that will disable transparent hugepages at boot:

```bash
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

```

Now update the system to use this script at boot and run it by executing the following commands:

```
chmod 755 /etc/init.d/disable-transparent-hugepages.sh
update-rc.d disable-transparent-hugepages.sh defaults
/etc/init.d/disable-transparent-hugepages.sh start

```

Repeat the steps in this section on each mongodb server before continuing to the next step.


## Install and Confiure MongoDB on all nodes [all nodes]

Next well will install the latest version of MongoDB on each of the servers. Execute the following commands on each server:

```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
sudo apt-get update
sudo apt-get install -y mongodb-org

```

Now prepare the /data volume, by running the following commands:

```bash
mkdir -p /data/db
mkdir -p /data/keys
chown -R mongodb:mongodb /data

```

Next put the 'mongodb.pem' in the correct place and instruct the system to trust our certificate authority. Execute the following commands:

```bash
cp cfssl/ca.pem /usr/local/share/ca-certificates/ca.crt
update-ca-certificates
cat cfssl/hicoriq-key.pem cfssl/hicoriq.pem > /etc/ssl/mongodb.pem

```

Edit the /etc/mongodb.conf file so the "storage", "systemLog:" and "net:" sections look exactly like the following:


```
# Where and how to store data.
storage:
  dbPath: /data
  journal:
    enabled: true

# where to write logging data.
systemLog:
  destination: syslog
  syslogFacility: daemon
  logRotate: reopen
  logAppend: true

# network interfaces
net:
  port: 27017
  bindIp: 0.0.0.0
  ssl:
    mode: requireSSL
    PEMKeyFile: /etc/ssl/mongodb.pem
```

You should have performed all of the above on all mongodb server nodes before moving on to the next section.


## Create the HICORIQ users and enable security [DB1 node only]

Note: This section is exclusively for db1. 

Create '/etc/systemd/system/mongodb.service' file by running the following command:

```
cat > /etc/systemd/system/mongodb.service << EOL
[Unit]
Description=High-performance, schema-free document-oriented database
After=network.target

[Service]
User=mongodb
ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf

[Install]
WantedBy=multi-user.target
EOL

```

Start mongodb, check it's status and enable it to start automatically at boot with the following commands:

```
systemctl start mongodb
systemctl status mongodb
systemctl enable mongodb

```

Next we need to create a private key that will be used to authenticate the replicas by executing the following commands:

```
openssl rand -base64 741 > /data/keys/mongodb-keyfile
chmod 600 /data/keys/mongodb-keyfile
chown mongodb:mongodb /data/keys/mongodb-keyfile

```

Next, let's create the mongodb admin and HICORIQ user accounts. Edit the following command so it has the fqdn of the DB1 node and the actual desired passwords and run it:


```
cat > create-users.js << EOL
conn = new Mongo("test-db1.hicoriq.net:27017");
db = conn.getDB("admin")

db.createUser( {
     user: "userAdmin",
     pwd: "**********",
     roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
   });

db.createUser( {
     user: "rootAdmin",
     pwd: "**********",
     roles: [ { role: "root", db: "admin" } ]
   });

db.createUser( {
     user: "hicoriq",
     pwd: "**********",
     roles: [ { role: "readWriteAnyDatabase", db: "admin" } ]
   });

db.createUser( {
     user: "hicoriqRead",
     pwd: "**********",
     roles: [ { role: "readAnyDatabase", db: "admin" } ]
   });
EOL

```

Now execute the create-users.js script against mongodb on DB1 by running the following command:

```
mongo --ssl --host test-db1.hicoriq.net create-users.js

```

The output of the above command should look like this:

```
MongoDB shell version v3.4.2
connecting to: mongodb://test-db1.hicoriq.net:27017/
MongoDB server version: 3.4.2
Successfully added user: {
        "user" : "userAdmin",
        "roles" : [
                {
                        "role" : "userAdminAnyDatabase",
                        "db" : "admin"
                }
        ]
}
Successfully added user: {
        "user" : "rootAdmin",
        "roles" : [
                {
                        "role" : "root",
                        "db" : "admin"
                }
        ]
}
Successfully added user: {
        "user" : "hicoriq",
        "roles" : [
                {
                        "role" : "readWriteAnyDatabase",
                        "db" : "admin"
                }
        ]
}
Successfully added user: {
        "user" : "hicoriqRead",
        "roles" : [
                {
                        "role" : "readAnyDatabase",
                        "db" : "admin"
                }
        ]
}
```

Now will our users in place, we must tell mongodb that we want to enable authentication, use the keyFile we generated and start a replica cluster. To do this edit /etc/systemd/system/mongodb.service and update the 'ExecStart' line to look exactly like this:

```
ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf --auth --keyFile /data/keys/mongodb-keyfile --replSet "rs0"

```

Now we must tell systemd to read the configuration and restart mongodb by running the following commands:

```
systemctl daemon-reload
systemctl restart mongodb

```

Now the user accounts in place and authentication turned on, test to verify that it's working by connecting with the 'mongo' client and logging in by running the following command:

```
mongo --ssl --host test-db1.hicoriq.net

```

This will place you in an interactive mongodb shell, the commands you enter in this shell are after the '>' prompt:

```
MongoDB shell version v3.4.2
connecting to: mongodb://test-db1.hicoriq.net:27017/
MongoDB server version: 3.4.2

> use admin
switched to db admin

> db.auth("rootAdmin", "**********")
1
> quit()
```

In the output above we can see that it accepted our username/password so we know that authenication is working.


Now we tell DB1 to initialize the replica set.  Run the following command, replacing the hostname with the fqdn of DB1 and the real password: 

```
cat > rs-init.js << EOL
conn = new Mongo("test-db1.hicoriq.net:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "**********");
rs.initiate();
EOL

```

Now execute the following command with the mongo client against DB1 (use the real fqdn):

```
mongo --ssl --host test-db1.hicoriq.net rs-init.js

```

## Prepare DB2 and DB3 to be replicas [DB2 and DB3 only]

Note: this section is for DB2 and DB3 nodes only 

Copy the '/data/keys/mongodb-keyfile' that we created earlier on DB1 to the same location on both DB2 and DB3 and then run the following commands:

```
chmod 600 /data/keys/mongodb-keyfile
chown mongodb:mongodb /data/keys/mongodb-keyfile

```

Create the systemd configuration to start mongodb by running the following command:

```
cat > /etc/systemd/system/mongodb.service << EOL
[Unit]
Description=High-performance, schema-free document-oriented database
After=network.target

[Service]
User=mongodb
ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf --auth --keyFile /data/keys/mongodb-keyfile --replSet "rs0"

[Install]
WantedBy=multi-user.target
EOL

```

Start mongodb, check it's status and enable it to start automatically at boot with the following commands:

```
systemctl start mongodb
systemctl status mongodb
systemctl enable mongodb

```

## Build the 3 node replica cluster

Run the folowing command on DB1, replacing the db1, db2 and db3 hostnames with the fqdns of your servers and the correct password:

```
cat > add-nodes.js << EOL
conn = new Mongo("test-db1.hicoriq.net:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "**********");
rs.add("test-db2.hicoriq.net");
rs.add("test-db3.hicoriq.net");
cfg = rs.conf()
cfg.members[0].priority = 1
cfg.members[1].priority = 0.5 
cfg.members[2].priority = 0.5 
rs.reconfig(cfg)
EOL

```

Now execute the following command with the mongo client on DB1:

```
mongo --ssl --host test-db1.hicoriq.net add-nodes.js

```

### Add DB2 as a secondary:

Execute the following command on DB2:

```
cat > enable-reads-on-db2.js << EOL
conn = new Mongo("test-db2.hicoriq.net:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "**********");
rs.slaveOk();
EOL

```

Now use the mongo client to execute this script:

```
mongo --ssl --host test-db2.hicoriq.net enable-reads-on-db2.js

```

### Add DB3 as a secondary:

Execute the following command on DB2:

```
cat > enable-reads-on-db3.js << EOL
conn = new Mongo("test-db3.hicoriq.net:27017");
db = conn.getDB("admin");
db.auth("rootAdmin", "**********");
rs.slaveOk();
EOL

```

Now use the mongo client to execute this script:

```
mongo --ssl --host test-db3.hicoriq.net enable-reads-on-db3.js

```


## Verify that the cluster is healthy

Run the following command to connect to DB1:

```
mongo --ssl --host test-db1.hicoriq.net
```

Below is the mongo shell, the commands that you should enter are after the "rs0:PRIMARY>" prompt:


```
MongoDB shell version v3.4.2
connecting to: mongodb://dev-db1:27017/
MongoDB server version: 3.4.2
rs0:PRIMARY> use admin
switched to db admin
rs0:PRIMARY> db.auth("rootAdmin", "**********")
1
rs0:PRIMARY> rs.status()
{
        "set" : "rs0",
        "date" : ISODate("2017-03-10T22:05:56.132Z"),
        "myState" : 1,
        "term" : NumberLong(1),
        "heartbeatIntervalMillis" : NumberLong(2000),
        "optimes" : {
                "lastCommittedOpTime" : {
                        "ts" : Timestamp(1489183555, 1),
                        "t" : NumberLong(1)
                },
                "appliedOpTime" : {
                        "ts" : Timestamp(1489183555, 1),
                        "t" : NumberLong(1)
                },
                "durableOpTime" : {
                        "ts" : Timestamp(1489183555, 1),
                        "t" : NumberLong(1)
                }
        },
        "members" : [
                {
                        "_id" : 0,
                        "name" : "dev-db1:27017",
                        "health" : 1,
                        "state" : 1,
                        "stateStr" : "PRIMARY",
                        "uptime" : 1257,
                        "optime" : {
                                "ts" : Timestamp(1489183555, 1),
                                "t" : NumberLong(1)
                        },
                        "optimeDate" : ISODate("2017-03-10T22:05:55Z"),
                        "electionTime" : Timestamp(1489182574, 2),
                        "electionDate" : ISODate("2017-03-10T21:49:34Z"),
                        "configVersion" : 4,
                        "self" : true
                },
                {
                        "_id" : 1,
                        "name" : "dev-db2.hicoriq.net:27017",
                        "health" : 1,
                        "state" : 2,
                        "stateStr" : "SECONDARY",
                        "uptime" : 358,
                        "optime" : {
                                "ts" : Timestamp(1489183555, 1),
                                "t" : NumberLong(1)
                        },
                        "optimeDurable" : {
                                "ts" : Timestamp(1489183555, 1),
                                "t" : NumberLong(1)
                        },
                        "optimeDate" : ISODate("2017-03-10T22:05:55Z"),
                        "optimeDurableDate" : ISODate("2017-03-10T22:05:55Z"),
                        "lastHeartbeat" : ISODate("2017-03-10T22:05:56.020Z"),
                        "lastHeartbeatRecv" : ISODate("2017-03-10T22:05:56.082Z"),
                        "pingMs" : NumberLong(0),
                        "syncingTo" : "dev-db1:27017",
                        "configVersion" : 4
                },
                {
                        "_id" : 2,
                        "name" : "dev-db3.hicoriq.net:27017",
                        "health" : 1,
                        "state" : 2,
                        "stateStr" : "SECONDARY",
                        "uptime" : 358,
                        "optime" : {
                                "ts" : Timestamp(1489183555, 1),
                                "t" : NumberLong(1)
                        },
                        "optimeDurable" : {
                                "ts" : Timestamp(1489183555, 1),
                                "t" : NumberLong(1)
                        },
                        "optimeDate" : ISODate("2017-03-10T22:05:55Z"),
                        "optimeDurableDate" : ISODate("2017-03-10T22:05:55Z"),
                        "lastHeartbeat" : ISODate("2017-03-10T22:05:55.935Z"),
                        "lastHeartbeatRecv" : ISODate("2017-03-10T22:05:55.109Z"),
                        "pingMs" : NumberLong(0),
                        "syncingTo" : "dev-db1:27017",
                        "configVersion" : 4
                }
        ],
        "ok" : 1
}
rs0:PRIMARY> 
```

In the output above you can see that DB1 is the primary based on the "rs0:PRIMARY>" prompt. DB2 and DB3's prompt will indicate that they are secondaries. We can see that all nodes are up, healtly and in either in a state of "PRIMARY" or "SECONDARY".
The DB1 has the highest priority, so it should always be the PRIMARY if it's up and healty. Conduct testing of the cluster by shutting down DB1 and verifiying that either DB2 of DB3 have taken over the role or PRIMARY. Then start DB1 again and verify that after a few minutes, that it assumes the role of PRIMARY again.

To view the replica set configuration, run the "rs.config()" command in the mongo shell: 


```
rs0:PRIMARY> rs.config()
{
        "_id" : "rs0",
        "version" : 4,
        "protocolVersion" : NumberLong(1),
        "members" : [
                {
                        "_id" : 0,
                        "host" : "test-db1:27017",
                        "arbiterOnly" : false,
                        "buildIndexes" : true,
                        "hidden" : false,
                        "priority" : 1,
                        "tags" : {

                        },
                        "slaveDelay" : NumberLong(0),
                        "votes" : 1
                },
                {
                        "_id" : 1,
                        "host" : "test-db2.hicoriq.net:27017",
                        "arbiterOnly" : false,
                        "buildIndexes" : true,
                        "hidden" : false,
                        "priority" : 0.5,
                        "tags" : {

                        },
                        "slaveDelay" : NumberLong(0),
                        "votes" : 1
                },
                {
                        "_id" : 2,
                        "host" : "test-db3.hicoriq.net:27017",
                        "arbiterOnly" : false,
                        "buildIndexes" : true,
                        "hidden" : false,
                        "priority" : 0.5,
                        "tags" : {

                        },
                        "slaveDelay" : NumberLong(0),
                        "votes" : 1
                }
        ],
        "settings" : {
                "chainingAllowed" : true,
                "heartbeatIntervalMillis" : 2000,
                "heartbeatTimeoutSecs" : 10,
                "electionTimeoutMillis" : 10000,
                "catchUpTimeoutMillis" : 2000,
                "getLastErrorModes" : {

                },
                "getLastErrorDefaults" : {
                        "w" : 1,
                        "wtimeout" : 0
                },
                "replicaSetId" : ObjectId("58c33e0cd853ea59814b4434")
        }
}
rs0:PRIMARY> quit()
```

That's it, the cluster setup is complete.

