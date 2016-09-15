#!/usr/bin/env python3

import subprocess
import sys
import pwd

import logging
import logging.handlers

protected_users = {
   'avahi', 'daemon', 'ganglia', 'haldaemon',
   'halevt', 'lp', 'messagebus', 'munge', 'nobody',
   'ntp', 'postfix', 'root', 'statd', 'syslog',
   'www-data', 'landscape', 'sshd', 'man', 'klog',
   'postgres'
}

def init_logging():
  crier = logging.getLogger('crybaby')
  crier.setLevel(logging.DEBUG)
  syslog = logging.handlers.SysLogHandler(
     address='/dev/log',
     facility='daemon'
  )
  crier.addHandler(syslog)

  crier.info('leftover starting')
  crier.debug('DEBUG: leftover syslog logging setup complete')

  return crier


def snapshot_process_table(crier):
  # initialize process table dictionary
  process_table = {}

  ps = subprocess.check_output(["ps", "-eo", "user:16,pid", "--noheaders"])
  for proc in ps.decode('ascii').split('\n'):
     psi = proc.split()
     if psi and psi[0] not in protected_users:
        try:
           pw_uid = pwd.getpwnam(psi[0]).pw_uid
        except KeyError:
           crier.info("no uid for %s", psi[0])
           pw_uid = -1

        if pw_uid < 5000:
           protected_users.add(psi[0])
           continue

        if psi[0] in process_table:
           process_table[psi[0]].append(psi[1])
        else:
           process_table[psi[0]] = [psi[1]]

  return process_table


def spawn_or_die(crier, cmd):
  try:
     result = subprocess.check_output(cmd)
  except subprocess.CalledProcessError as err:
     crier.critical(
        'CRITICAL: %s command failed with %s %s', cmd[0],
        err.errno,
        err.strerror
     )
     sys.exit(1)

  return result.decode('ascii')

def get_slurm_aliases(crier):
  result=spawn_or_die(crier,['scontrol','show','aliases'])

  return ','.join(result.split())

def get_slurm_users(crier):
  nodenames=get_slurm_aliases(crier)
  result=spawn_or_die(crier,['squeue','-a','-h','-w',nodenames,'-o','%u'])

  return(set(result.split()))

def kill_user_procs(procs,crier):
  for proc in procs:
     try:
        subprocess.check_call(['kill','-9',proc])
     except subprocess.CalledProcessError as err:
        crier.info("leftover: kill %s returns error %s" % (proc, err))

def main(args):
  crier=init_logging()

  proc_tbl=snapshot_process_table(crier)
  slurm_users=get_slurm_users(crier)

  for users,procs in proc_tbl.items():
     if users not in slurm_users:
        crier.info('leftover: killing all processes run by %s' % users)
        kill_user_procs(procs,crier)

if __name__ == '__main__':
   main(sys.argv[1:])
