# S3-md5verify

To use this script the following conditions must be met:

- Linux operating system
- Python 2.7 or higher installed
- The aws-cli (https://github.com/aws/aws-cli) installed and configured with the appropriate credentials.
- An S3 bucket containing the data that you wish to verify.
- Each directory containing data must have a "checksum" folder containg checksum files for the parent directory.
- The checksum files must be the same name as the coresponding data file but with a .md5 extension added.
- The checksum files must contain the md5 checksum data in the same output format used by the 'md5sum' command.
- The local directory designated to use for the download and verification need to be at least as large as the largest object in the bucket.

In addtion to the above requirements, it's best if you use and EC2 instance with enhanced networking support (10Gb/s) that is properly enabled (http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enhanced-networking.html#enabling_enhanced_networking). You'll also get much better transfer performance if your VPC has an S3 endpoint configured (http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/vpc-endpoints.html). If you run this from an instance located on Campus, it will take forever and burn up the internet connection if used with a large dataset; it will also be expensive as you will be paying for egress.

###Usage: 

```
./s3-md5verify.py <bucket> <path> <tempdir>
```

###Example:

Here is an example of a command that was run against actual data. It will be verifying data located under the 'readonly/P01CA91955-WGS80/Project_REI_11321_B01_SOM_WGS.2016-04-12/' path in the 's3://fh-pi-reid-b' bucket, using '/data' as the temporary data download/verfication working directory:

```
./s3-md5verify.py s3://fh-pi-reid-b readonly/P01CA91955-WGS80/Project_REI_11321_B01_SOM_WGS.2016-04-12/ /data/
```
