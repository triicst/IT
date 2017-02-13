#!/usr/bin/python
import os
import sys

awscli = "/usr/bin/aws"
md5sum = "/usr/bin/md5sum"


def getfilelist(bucketpath):
    """Gets, cleans up and returns a list of the object under the provided bucketpath""" 
    fls = os.popen("%s s3 ls --recursive %s" % (awscli, bucketpath)).readlines()
    fls = [" ".join(x.strip().split()[3:]) for x in fls]
    return fls


def main():
    bucket = sys.argv[1]
    if not bucket.endswith('/'):
        bucket += '/'
    path = sys.argv[2]
    if not path.endswith('/'):
        path += '/'
    tempdir = sys.argv[3]
    if not tempdir.endswith('/'):
        tempdir += '/'
    bucketpath = bucket + path
    bucketcontents = getfilelist(bucketpath)
    md5s, files = getmd5s(bucketcontents)
    missing, filemap = checkfiles(md5s, files)

    # If any files are missing, print report of missing files
    if missing:
        missingreport(missing, list(filemap))

    md5check(filemap, bucket, bucketpath, tempdir)


def md5check(filemap, bucket, bucketpath, tempdir):
    """Compare the reported md5sum to the actual md5sum to make sure they match and write report to file"""
    count = 0
    report = open("%s-md5report.csv" % bucketpath[:-1].replace('s3://','').replace('/','_'), 'a')
    print("%s, %s, %s, %s" % ("file", "reported-md5", "actual-md5", "match"))
    report.write("%s, %s, %s, %s\n" % ("file", "reported-md5", "actual-md5", "match"))
    report.flush()
    for f in filemap:
        count += 1
        os.popen("%s s3 cp \"%s\" \"%s%s\"" % (awscli, bucket + filemap[f], tempdir, filemap[f].split('/')[-1])).read().strip()
        md5rpt = open("%s%s" % (tempdir, filemap[f].split('/')[-1])).read().strip().split()[0]
        os.popen("%s s3 cp \"%s\" \"%s%s\"" % (awscli, bucket + f, tempdir, f.split('/')[-1])).read().strip()
        md5act = os.popen("%s \"%s%s\"" % (md5sum, tempdir, f.split('/')[-1])).read().strip().split()[0]
        print("%s%s, %s, %s, %s" % (bucket, f, md5rpt, md5act, md5rpt == md5act))
        report.write("%s%s, %s, %s, %s\n" % (bucket, f, md5rpt, md5act, md5rpt == md5act))
        os.remove("%s%s" % (tempdir, filemap[f].split('/')[-1]))
        os.remove("%s%s" % (tempdir, f.split('/')[-1]))
        report.flush()


def getmd5s(bucketcontents):
    """Returns two lists, one of the md5 files and the other all non-md5 files"""
    md5 = [] 
    files = []

    for l in bucketcontents:
        if l.endswith('.md5'):
            md5.append(l)
        else:
            files.append(l)

    return md5, files 


def checkfiles(md5s, files):
    """Returns a lists if any missing files and a map of the files to their corresponding data file"""
    missing = []
    filemap = {}

    for f in md5s:
        fn = f.replace('.md5','').replace('checksum/','')
        if fn not in files:
            missing.append(fn)
        else:
            filemap[fn] = f

    return missing, filemap


def missingreport(missing, match):
    """Prints a report of missing data files"""
    if missing:
        print("Checksum files with matching data files: %s\nChecksum files missing corresponding data file: %s\n" % (len(match), len(missing))) 

        print("Missing files:")
        for m in range(1, len(missing) + 1):
            print("%s: %s" % (m, missing[m -1]))
    else:
        print("No missing datafiles")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: %s <bucket> <path> <tempdir>" % sys.argv[0])
        sys.exit(1)
    main()
