#!/usr/bin/python3
import boto3    
import json
import os


def get_regions():
    regions = []
    ec2 = boto3.client('ec2', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    response = ec2.describe_regions()
    for region in response['Regions']:
        regions.append(region['RegionName']) 
    return(regions)

def get_instances(region):
    instances = []
    ec2client = boto3.client('ec2', region_name=region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    response = ec2client.describe_instances()
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(instance)
    return(instances)


def removebadchars(token):
    translate = {'$': '', '&': '', '#': '', '*': '', '(': '', ')': '', '[': '', ']': '', ' ': '',
                '?': '','^': '', '`': '', '~': '', '{': '', '}': '', ',': '', '|': '', ':': '', ';': '', "'": '', '"': ''}
    for char in translate:
        token = token.replace(char, translate[char])
    return(token)


def create_objects(instances):
    objects = []
    for instance in instances:
        i  = Instance()
        i.AvailabilityZone = instance["Placement"]["AvailabilityZone"]
        i.InstanceId = instance["InstanceId"]
        i.InstanceType = instance["InstanceType"]
        i.State = instance["State"]["Name"]
        i.ImageId = instance["ImageId"]
        i.LaunchTime = str(instance["LaunchTime"])
        i.Region = i.AvailabilityZone[0:-1]
        try:
            i.PrivateIpAddress = instance["PrivateIpAddress"]
        except:
            i.PrivateIpAddress = ""
        try:
            i.KeyName = instance["KeyName"]
        except:
            i.KeyName = ""
        try:
            i.PublicIpAddress = instance["PublicIpAddress"]
        except:
            i.PublicIpAddress = ""
        try:
            i.SubnetId = instance["SubnetId"]
        except:
            i.SubnetId = ""
        try:
            i.VpcId = instance["VpcId"]
        except:
            i.VpcId = ""

        for tag in instance["Tags"]:
            if tag['Key'].lower() == 'owner':
                i.Owner = removebadchars(tag['Value'].lower()) 
            elif tag['Key'].lower() == 'name':
                i.Name = removebadchars(tag['Value'].lower())
            elif tag['Key'].lower() == 'technical_contact':
                i.TechnicalContact = removebadchars(tag['Value'].lower())

        if not "TechnicalContact" in i.__dict__:
            i.TechnicalContact = 'missing'
        if not "Owner" in i.__dict__:
            i.Owner = 'missing'
        if not "Name" in i.__dict__:
            i.Name = 'missing'
        
        objects.append(i)

    return(objects)

    

def main():
    instances = []
    states = {}
    types = {}
    azs = {}
    owners = {}

    for region in get_regions():
        instances.extend(get_instances(region))
    objects = create_objects(instances)
    instance_count = len(instances)
    for i in objects:
        states[i.State] = states.setdefault(i.State, 0) + 1        
        owners[i.Owner] = owners.setdefault(i.Owner, 0) + 1        
        azs[i.AvailabilityZone] = azs.setdefault(i.AvailabilityZone, 0) + 1        
        types[i.InstanceType] = types.setdefault(i.InstanceType, 0) + 1        

    mtype = "# TYPE ec2_instance_states_%s gauge"
    metric = "ec2_instance_states_%s{state=\"%s\",account=\"%s\"} %d"

    print(mtype % account)
    for k in states:
        print(metric % (account, k, account, states[k]))

    mtype = "# TYPE ec2_instance_types_%s gauge"
    metric = "ec2_instance_types_%s{type=\"%s\",account=\"%s\"} %d"


    print(mtype % account)
    for k in types:
        print(metric % (account, k, account, types[k]))

    mtype = "# TYPE ec2_instance_zones_%s gauge"
    metric = "ec2_instance_zones_%s{az=\"%s\",account=\"%s\"} %d"

    print(mtype % account)
    for k in azs:
        print(metric % (account, k, account, azs[k]))

    mtype = "# TYPE ec2_instance_owners_%s gauge"
    metric = "ec2_instance_owners_%s{owner=\"%s\",account=\"%s\"} %d"

    print(mtype % account)
    for k in owners:
        print(metric % (account, k, account, owners[k]))


class Instance:
    def toJSON(self):
        return(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4))

if __name__ == "__main__":
    region_name='us-west-2'
    account = ''
    aws_access_key_id=''
    aws_secret_access_key=''
    main()
