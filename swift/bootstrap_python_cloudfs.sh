#! /bin/bash

# bootstrapping python and sftp-cloudfs
# typically you would run this from the 
# home directory of the service account
# you want to run sftp-cloudfs as.

installdir=~/cloudfs
authurl=https://host.domain.com/auth/v1.0
if ! [[ -z $1 ]]; then
  authurl=$1
fi

echo "install sftp-cloudfs into $installdir..."

# bootstrapping python

export LD_LIBRARY_PATH=$installdir/python/2.7/lib:$LD_LIBRARY_PATH
export PATH=~/bin:$installdir/python/2.7/bin/:$PATH

mkdir -p $installdir/setup
cd $installdir/setup
wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
tar xvfz Python-2.7.9.tgz
cd Python-2.7.9
./configure --enable-shared --prefix=$installdir/python/2.7 LDFLAGS="-L/$installdir/python/2.7/lib -Wl,-rpath /lib"
make; make install
wget https://bootstrap.pypa.io/get-pip.py -O - | python

#installing sftp-cloudfs 
$installdir/python/2.7/bin/pip install python-daemon==1.6.1
$installdir/python/2.7/bin/pip install git+https://github.com/openstack/python-swiftclient
$installdir/python/2.7/bin/pip install sftp-cloudfs

#configuring sftp-cloudfs 
mkdir -p $installdir/.ssh
mkdir -p $installdir/etc
mkdir -p $installdir/var/log
mkdir -p $installdir/var/run

ssh-keygen -f $installdir/.ssh/id_rsa -N '' -t rsa

echo "[sftpcloudfs]" > $installdir/etc/sftpcloudfs.conf
echo "auth-url = $authurl" >> $installdir/etc/sftpcloudfs.conf
echo "host-key-file = $installdir/.ssh/id_rsa" >> $installdir/etc/sftpcloudfs.conf
echo "bind-address = 0.0.0.0" >> $installdir/etc/sftpcloudfs.conf
echo "split-large-files = 2000" >> $installdir/etc/sftpcloudfs.conf
echo "hide-part-dir = yes" >> $installdir/etc/sftpcloudfs.conf
echo "log-file = $installdir/var/log/sftpcloudfs.log" >> $installdir/etc/sftpcloudfs.conf
echo "pid-file = $installdir/var/run/sftpcloudfs.pid" >> $installdir/etc/sftpcloudfs.conf

echo "#! /bin/bash" > $installdir/sftpcloudfs.sh
echo "export LD_LIBRARY_PATH=$installdir/python/2.7/lib:$LD_LIBRARY_PATH" >> $installdir/sftpcloudfs.sh
echo "export PATH=~/bin:$installdir/python/2.7/bin/:$PATH" >> $installdir/sftpcloudfs.sh
echo "sftpcloudfs --config=$installdir/etc/sftpcloudfs.conf" >> $installdir/sftpcloudfs.sh
chmod +x $installdir/sftpcloudfs.sh

echo "now starting ... sftpcloudfs --config=$installdir/etc/sftpcloudfs.conf"
$installdir/sftpcloudfs.sh


