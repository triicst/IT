## Oncoscape MongoDB Cluster Setup

These instructions will build a three node MongoDB replica cluster. 

###1. Create three EC2 instances running Ubuntu 14.04

On Nimbus, copy the following commands below and paste them in PowerShell ISE, modify the parameters, subnets and security groups to match your situation and run it. 
 
```powershell
Set-Location -Path O:\scripts\aws

# Create first node in AZA
.\ec2-provision-instance-linux.ps1 -Name mongo-db1 `
    -InstanceType t2.micro `
    -RootVolSize 50 `
    -RootVolType gp2 `
    -RootVolDelOnTerminate false `
    -DataVolSize 100 `
    -DataVolType gp2 `
    -DataVolDelOnTerminate false `
    -DataVolEncrypted false `
    -DailySnapshotRetention 7 `
    -RegisterDNS true `
    -Owner _hb/sttr `
    -TechContact rmcdermo@fredhutch.org `
    -BillingContact cloudops@fredhutch.org `
    -Description "MonogoDB Server Zone A" `
    -Phi no -Pii no -PubliclyAccessible no `
    -BusinessHours 24x7 `
    -GrantCritical no `
    -AlertsEnabled true `
    -SubnetId subnet-fb40408c `
    -SecurityGroupIds sg-b28b0ad4

# Create second node in AZB
.\ec2-provision-instance-linux.ps1 -Name mongo-db2`
    -InstanceType t2.micro `
    -RootVolSize 50 `
    -RootVolType gp2 `
    -RootVolDelOnTerminate false `
    -DataVolSize 100 `
    -DataVolType gp2 `
    -DataVolDelOnTerminate false `
    -DataVolEncrypted false `
    -DailySnapshotRetention 7 `
    -RegisterDNS true `
    -Owner _hb/sttr `
    -TechContact rmcdermo@fredhutch.org `
    -BillingContact cloudops@fredhutch.org `
    -Description "MonogoDB Server Zone B" `
    -Phi no -Pii no -PubliclyAccessible no `
    -BusinessHours 24x7 `
    -GrantCritical no `
    -AlertsEnabled true `
    -SubnetId subnet-be36dada `
    -SecurityGroupIds sg-b28b0ad4

#  Create third node also in AZB
.\ec2-provision-instance-linux.ps1 -Name mongo-db3 `
    -InstanceType t2.micro `
    -RootVolSize 50 `
    -RootVolType gp2 `
    -RootVolDelOnTerminate false `
    -DataVolSize 100 `
    -DataVolType gp2 `
    -DataVolDelOnTerminate false `
    -DataVolEncrypted false `
    -DailySnapshotRetention 7 `
    -RegisterDNS true `
    -Owner _hb/sttr `
    -TechContact rmcdermo@fredhutch.org `
    -BillingContact cloudops@fredhutch.org `
    -Description "MonogoDB Server Zone B2" `
    -Phi no -Pii no -PubliclyAccessible no `
    -BusinessHours 24x7 `
    -GrantCritical no `
    -AlertsEnabled true `
    -SubnetId subnet-be36dada `
    -SecurityGroupIds sg-b28b0ad4
```

###2. Building the MongoDB cluster

After your EC2 nodes are up and running, edit the "create-mongodb-cluster.sh" to set the hostname and password variables to the desired values:

```bash
# Variables 
db1=mongo-db1
db2=mongo-db2
db3=mongo-db3
userAdminPasswd=P@ssword
rootAdminPasswd=P@ssword
oncoscapePasswd=P@ssword
oncoscapeReadPasswd=P@ssword
```

***Note:*** The above passwords map to the following mongo user accounts and roles: 

| Mongo Users   | Password Variable     | Mongo Role           |
|:--------      |:--------              |:--------             |
| rootAdmin     | rootAdminPassword     | root                 |
| userAdmin     | userAdminPassword     | userAdminAnyDatabase | 
| oncoscape     | oncoscapePassword     | readWriteAnyDatabase |
| oncoscapeRead | oncoscapeReadPassword | readAnyDatabase      |


After editing the varibles in "create-mongodb-cluster.sh" script, SCP it to the first node (mongo-db1 in this example). Next, SSH to it (mongo-db1) and run the following commands:

```bash
chmod 755 create-mongodb-cluster.sh

sudo ./create-mongodb-cluster.sh
```

The script should take about 5 minutes to complete... 

When complete, you should now have a three node replica cluster with mongo-db1 as the favored primary (read/write) with the secondaries mongo-db2, mongo-db3 serving a read replicas that can take over the primary node role until mongo-db1 returns to service.

  
