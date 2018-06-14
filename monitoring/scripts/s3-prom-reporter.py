#!/usr/bin/python3
from datetime import datetime, timedelta
import boto3


def main():
    cloudwatch = boto3.client('cloudwatch', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    paginator = cloudwatch.get_paginator('list_metrics')
    s3 = boto3.client("s3", region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    buckets = s3.list_buckets()['Buckets']
    buckets = [x['Name'] for x in buckets]

    totalStd = 0
    totalIAS = 0
    first_metric = True 

    for bucket_name in buckets:
        for s3class in ('StandardStorage','StandardIAStorage'):
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {
                        "Name": "BucketName",
                        "Value": bucket_name
                    },
                    {
                        "Name": "StorageType",
                        "Value": s3class 
                    }
                ],
                StartTime=datetime.now() - timedelta(days=2),
                EndTime=datetime.now(),
                Period=86400,
                Statistics=['Average']
            )  


            if not response['Datapoints']:
                continue
            #bucket_size_bytes = response['Datapoints'][-1]['Average']
            bucket_size_bytes = response['Datapoints']

            # This if/else makes sure that if more than one datapoint is returned, the latest data point is selected and used.
            if len(bucket_size_bytes) == 1:
                bucket_size_bytes = bucket_size_bytes[0]['Average']
            else: # more than one metrics was returned for this bucket/range, we need find the latest metric
                dates = [] 
                latest = (datetime.now() - timedelta(days=365))
                for x in range(len(bucket_size_bytes)):
                    dates.append(bucket_size_bytes[x]['Timestamp'])
                for x in dates:
                    if x.replace(tzinfo=None) > latest.replace(tzinfo=None):
                        latest = x
                bucket_size_bytes = bucket_size_bytes[dates.index(latest)]['Average'] # get the latest metric

            if s3class == "StandardStorage":
                totalStd += bucket_size_bytes
            elif s3class == "StandardIAStorage":
                totalIAS += bucket_size_bytes
            
            if (bucket_size_bytes) > 262144: # only report if bucket size is more than 256KB
                if first_metric:
                    print("# TYPE s3bucketsize gauge")
                    first_metric = False
                print("s3bucketsize{{account=\"hse\",bucketname=\"{}\",class=\"{}\"}} {}".format(bucket_name, s3class, bucket_size_bytes))

    if totalStd > 262144:
        print("# TYPE s3bucketsize_total gauge")
        print("s3bucketsize_total{{account=\"hse\",class=\"StandardStorage\"}} {}".format(totalStd))
        print("s3bucketsize_total{{account=\"hse\",class=\"StandardIAStorage\"}} {}".format(totalIAS))


if __name__ == "__main__":
    region_name='us-west-2'
    account = ''
    aws_access_key_id=''
    aws_secret_access_key=''
    main()
