#!/usr/bin/python
"""
Generates a temporary URL that can be used to download objects from S3 for a limited amount of time.
"""
import sys
import boto3

def genURL(bucketname, filename, days):
    expiresIn = int(days) * 86400
    client = boto3.client('s3')
    url = client.generate_presigned_url('get_object', Params = {'Bucket': bucketname, 'Key': filename}, ExpiresIn = expiresIn, )
    return(url)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("\nUSAGE: {0} bucketname filename linkLifeInDays\n".format(sys.argv[0]))
        sys.exit(1)
    bucketname = sys.argv[1]
    filename = sys.argv[2]
    days = sys.argv[3]
    signedURL = genURL(bucketname, filename, days)
    print("\n{0}\n".format(signedURL))
