#!/bin/bash
cat /etc/motd.template >/etc/motd
echo -n "Least used systems as of ">>/etc/motd
date >>/etc/motd
/usr/local/bin/wtb -s >>/etc/motd
