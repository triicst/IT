#! /usr/bin/env python3

import boto3

print('boto3 version: ', boto3.__version__)

session = boto3.session.Session(profile_name='s3.fhcrc.org')
s3 = session.resource('s3',
    endpoint_url='https://s3.fhcrc.org',
    config=boto3.session.Config(signature_version='s3v4'))

l = list(s3.buckets.all())
print ('bucket / container list: %s' % l)

# create a Bucket
mybucket = s3.create_bucket(Bucket='mytestbucket1')

# or if it is already there 
#mybucket = s3.Bucket('mytestbucket')

# upload a file
mybucket.upload_file('/tmp/sys_status.rpt', '/tmp/sys_status.rpt.txt')

