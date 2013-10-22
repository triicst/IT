#!/usr/bin/env python

import subprocess
import socket
import sys
import logging
import logging.handlers
from time import sleep

crier = logging.getLogger('crybaby')
crier.setLevel( logging.DEBUG )
syslog = logging.handlers.SysLogHandler(
    address = '/dev/log',
    facility='daemon'
)
crier.addHandler( syslog )

crier.info( 'leftover starting' )
crier.debug( 'DEBUG: leftover syslog logging setup complete' )

protected_users = (
    'avahi', 'daemon', 'ganglia', 'haldaemon',
    'halevt', 'lp', 'messagebus', 'munge', 'nobody',
    'ntp', 'postfix', 'root', 'statd', 'syslog',
    'www-data', 'landscape', 'sshd', 'man', 'klog',
)

cmd = [ 'squeue', '-a', '-h', '-w', socket.gethostname(), '-o', '%u']
try:
    result = subprocess.check_output( cmd )
except subprocess.CalledProcessError as err:
    crier.critical(
        'CRITICAL: squeue command failed with %s %s',
        err.errno,
        err.strerror
    )
    sys.exit(1)


valid_users = set(result.rstrip('\n').split('\n'))
valid_users = valid_users.union( protected_users )

cmd = [ 'ps', '--no-headers', '-e', '-o', 'user' ]
result = subprocess.check_output( cmd )
running_users = set(result.rstrip('\n').split('\n'))

invalid_users = running_users.difference( valid_users )
invalid_users.add('petersen')

if len( invalid_users ) == 0:
    crier.debug('DEBUG: leftover found no users with invalid jobs,' +
                'len(invalid_users)=%s', len(invalid_users) )
    exit

for u in invalid_users:
    crier.info( 'killing processes belonging to user %s', u )
    cmd = [ 'pkill', '-TERM', '-u', u ]
    try:
        result = subprocess.check_output( cmd )
    except subprocess.CalledProcessError as err:
        crier.debug( 'pkill exited with %s %s', err.returncode, err.message )
        crier.error( 'ERROR: pkill could not TERM processes from %s', u )
        continue

    sleep( 8 )

    cmd = [ 'pkill', '-KILL', '-u', u ]
    try:
        result = subprocess.check_output( cmd )
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            crier.debug( "DEBUG: pkill exited non-zero," +
                        "no processes left to kill" )
            continue
        else:
            crier.debug(
                'DEBUG: pkill exited with %s %s', err.returncode, err.message
            )
            crier.error( 'ERROR: pkill could not KILL processes from %s', u )
            continue



