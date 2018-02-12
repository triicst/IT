# goports

Simple TCP port scanner written in Golang

## Usage

```
Usage: ./goports [-t <cpu threads> -c <concurrency> -to <timeout in ms> -v] -ip <ip or cidr> -p <ports>

Example: ./goports -ip 192.168.73.1/28 -p 22,80,443,8000-8100

  -c int
  	Optional: set number of concurrent port open operations to use; defaults to 32 per logical CPU (default 128)
  
  -ip string
    	Required: IP address or CIDR block to scan

  -p string
    	Required: Set of ports to scan; individal ports separated by "," port ranges separated by "-" (22,80,8000-8100)

  -t int
    	Optional: set number of CPU threads to use; defaults to the number of logical CPUs in your system (default 4)

  -to int
    	Optional: Specify the amount of time to wait in milliseconds; defaults to 100  (default 100)

  -q	Optional: quiet mode; suppress the summary report

  -v	Optional: Turn on verbose output mode; shows both open and closed ports

  -h	print usage information
```

## Output

```
./goports -ip 192.168.0.0/16 -p 80

...
192.168.73.193 2701 open
192.168.73.193 3389 open
192.168.193 5985 open
192.168.200 139 open
192.168.200 135 open
192.168.200 445 open
192.168.200 5985 open
192.168.73.200 2701 open
192.168.73.241 22 open
192.168.73.241 139 open
192.168.73.241 445 open
192.168.73.247 23 open

Hosts scanned: 65534
Ports scanned: 65534
Elapsed time: 0.91 seconds
Scan Rates:
    ports/s: 71719.34
    hosts/s: 71719.34
```
