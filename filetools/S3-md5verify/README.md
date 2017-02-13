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

###Output Report

While the script is running it will print the progress on the standard out, but it will also create a CSV report file in the same directory that the script is run. The name of the report file with be the name S3 path provided and end with "-md5report.csv". The output format is the name of the file, the reported md5, the actual md5sum and boolean match field indicating is the file is good. Here is some example output. Notice that one file (five.bam) is bad:

```
file, reported-md5, actual-md5, match
s3://bucket/path/one.bam,   0ce217ce569ec14281d8d8b1a36f0e57, 0ce217ce569ec14281d8d8b1a36f0e57, True
s3://bucket/path/two.bam,   edeaa47ac5a54568234af23cef33b1c9, edeaa47ac5a54568234af23cef33b1c9, True
s3://bucket/path/three.bam, 8834259798509088e71d871d31429150, 8834259798509088e71d871d31429150, True
s3://bucket/path/four.bam,  0a93da18df58071843ea9a8b29620f37, 0a93da18df58071843ea9a8b29620f37, True
s3://bucket/path/five.bam,  8c892a90d17cb5690fa51fa95a9e0c83, 5c26892904d14723c23b5690fa51fa98, False
s3://bucket/path/six.bam,   458fcab7a9439713aa36a7edc26c86fa, 458fcab7a9439713aa36a7edc26c86fa, True
s3://bucket/path/seven.bam, 7ec4e18e96423306559f7fa94f7ed0f8, 7ec4e18e96423306559f7fa94f7ed0f8, True
s3://bucket/path/eight.bam, b21a6f8e18c8959c93de71615b7080aa, b21a6f8e18c8959c93de71615b7080aa, True
s3://bucket/path/nine.bam,  369ac0f81e29f1fa11ec713e0cff3858, 369ac0f81e29f1fa11ec713e0cff3858, True
s3://bucket/path/ten.bam,   6be0f41eb43d48cc2143188b9a932ce5, 6be0f41eb43d48cc2143188b9a932ce5, True
...
```
