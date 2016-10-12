#! /bin/bash

PATH=lf_backup:$PATH
lf-backup /fh/fast /bam-lf-backup-tests
swc rm -rf /bam-lf-backup-tests
