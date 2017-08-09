# CIFSBAST


- Application: Cifsblast
- Version: 1.0
- Requires: Unix (Linux, Solaris, Mac) OS, smbclient binary, Python 2.6+
- Purpose: Generate a very high volume of CIFS write IO to stress networks and storage systems.
- Authors: Robert McDermott <rmcdermo@fhcrc.org>, Supriatno Agus <sagus@fhcrc.org>
- last updated: 2012-04-03


```
Usage: cifsblast.py --server=//server/share --username=DOMAIN/username  --localdir=dir --remotedir=dir --jobs=integer (defaults to 100) --threads=integer  (defaults to system CPU core count + 2 ) [--password=userpassword (optional)]  [--buffersize=bytes (min 16384, max 16776960, default 64512 (optional)]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -s SERVER, --server=SERVER
                        The CIFS server and share you want to use.
  -u USERNAME, --username=USERNAME
                        The username to connect with; format DOMAIN/username.
  -p PASSWORD, --password=PASSWORD
                        The provided users password. Optional; if not provided
                        you'll be prompted for the password
  -l LOCALDIR, --localdir=LOCALDIR
                        The local directory to copy to the server.
  -r REMOTEDIR, --remotedir=REMOTEDIR
                        The local directory to copy to the server.
  -j NUM_JOBS, --jobs=NUM_JOBS
                        The total number of copy jobs to run; requires a
                        integer. Defaults to 100 jobs.
  -t NUM_PROCESSES, --threads=NUM_PROCESSES
                        The total number of parallel jobs to run; requires a
                        integer; defaults to the number of CPU     cores in
                        the system + 2.
  -b BUFFERSIZE, --buffersize=BUFFERSIZE
                        Smbclient uses an internal memory buffer by default of
                        size 64512 bytes. This command allows this     size to
                        be set to any range between 16384 bytes (16KB) and
                        16776960 bytes (64MB) (Optional).
```
