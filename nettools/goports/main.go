// Simple concurrent TCP port scanning utiliy
package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

// scanResult type to hold the result of each port that is scanned
type scanResult struct {
	Port    int
	Success bool
}

func main() {
	// define and set default command parameter flags
	var ipFlag = flag.String("ip", "", "Required: IP address or CIDR block to scan")
	var pFlag = flag.String("p", "", "Required: Set of ports to scan; individal ports separated by \",\" port ranges separated by \"-\" (22,80,8000-8100)")
	var toFlag = flag.Int("to", 100, "Optional: Specify the amount of time to wait in milliseconds; defaults to 100 ")
	var tFlag = flag.Int("t", runtime.NumCPU(), "Optional: set number of CPU threads to use; defaults to the number of logical CPUs in your system")
	var cFlag = flag.Int("c", runtime.NumCPU()*32, "Optional: set number of concurrent port open operations to use; defaults to 32 per logical CPU")
	var vFlag = flag.Bool("v", false, "Optional: Turn on verbose output mode; shows both open and closed ports")
	var qFlag = flag.Bool("q", false, "Optional: quiet mode; suppress the summary report")
	var hFlag = flag.Bool("h", false, "print usage information")

	// usage function that's executed if a required flag is missing or user asks for help (-h)
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "\nUsage: %s [-t <cpu threads> -c <concurrency> -to <timeout in ms> -v] -ip <ip or cidr> -p <ports>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "\nExample: %s -ip 140.107.73.1/28 -p 22,80,443,8000-8100\n\n", os.Args[0])
		flag.PrintDefaults()
		fmt.Println()
	}
	flag.Parse()

	// provide help (-h)
	if *hFlag == true {
		flag.Usage()
		os.Exit(0)
	}

	// the -ip flag is required
	if *ipFlag == "" {
		fmt.Fprintf(os.Stderr, "\nMissing required -ip (ip or cidr) argument\n\n")
		flag.Usage()
		os.Exit(2)
	}

	// the -p flag is required
	if *pFlag == "" {
		fmt.Fprintf(os.Stderr, "\nMissing required -p (ports) argument\n\n")
		flag.Usage()
		os.Exit(2)
	}

	// set the number of CPU threads to use as provided by the -t flag
	runtime.GOMAXPROCS(*tFlag)
	wg := new(sync.WaitGroup)

	// counting semaphore to limit concurrency, defalts to 256, but can be adjust with the -c flag
	sema := make(chan struct{}, *cFlag)

	// parse the ports provided my user via the -p flag into a slice of its
	ports, err := parsePorts(pFlag)
	if err != nil {
		log.Fatal(err)
	}

	// slice to hold all IP addresses to scan
	ips := []string{}

	// populate ips slice with all the IP addresses to scan as provided by the -ip flag
	if !strings.Contains(*ipFlag, "/") || strings.Contains(*ipFlag, "/32") {
		ips = append(ips, *ipFlag) //single IP address provided to scan
	} else {
		// range of IP addresses to scan provided
		ipss, err := hosts(*ipFlag)
		if err != nil {
			log.Fatal(err)
		}
		ips = ipss
	}

	// about do do some work, start the timer
	start := time.Now()

	// interate over IP addresses and scan defined ports for each IP concurrently
	for _, ip := range ips {
		for _, p := range ports {
			wg.Add(1)
			go scanPort(ip, p, wg, sema, toFlag, vFlag)
		}
	}

	// wait for all goroutines to complete
	wg.Wait()

	// work is done, stop the timer
	elapsed := time.Since(start)

	// provide summary report if user wants one
	if *qFlag == false {
		fmt.Printf("\nHosts scanned: %d\n", len(ips))
		fmt.Printf("Ports scanned: %d\n", len(ports)*len(ips))
		fmt.Printf("Elapsed time: %0.2f seconds\n", elapsed.Seconds())
		fmt.Println("Scan Rates:")
		fmt.Printf("    ports/s: %0.2F\n", float64(len(ports)*len(ips))/elapsed.Seconds())
		fmt.Printf("    hosts/s: %0.2F\n", float64(len(ips))/elapsed.Seconds())
	}
}

// parsePorts parses the input provided by the user "-p 22,80,8000-8080" and returns a flat slice of ints, one per port
func parsePorts(pFlag *string) ([]int, error) {
	parts := strings.Split(*pFlag, ",")
	ports := []int{}
	for _, part := range parts {
		if strings.Contains(part, "-") {
			p := strings.Split(part, "-")
			start, err := strconv.Atoi(p[0])
			if err != nil {
				return nil, err
			}
			end, err := strconv.Atoi(p[1])
			if err != nil {
				return nil, err
			}
			for x := start; x <= end; x++ {
				ports = append(ports, x)
			}
		} else {
			p, _ := strconv.Atoi(part)
			ports = append(ports, p)
		}
	}
	return ports, nil
}

func inc(ip net.IP) {
	for j := len(ip) - 1; j >= 0; j-- {
		ip[j]++
		if ip[j] > 0 {
			break
		}
	}
}

// hosts takes cidr string provided by -ip flag and return a slide of all IP addreses in the range
func hosts(cidr string) ([]string, error) {
	ip, ipnet, err := net.ParseCIDR(cidr)
	if err != nil {
		return nil, err
	}

	var ips []string
	for ip := ip.Mask(ipnet.Mask); ipnet.Contains(ip); inc(ip) {
		ips = append(ips, ip.String())
	}
	// remove network address and broadcast address
	return ips[1 : len(ips)-1], nil
}

// scanPort connects to each IP and port and prints the results to stdout
func scanPort(host string, port int, wg *sync.WaitGroup, sema chan struct{}, timeout *int, verbose *bool) *scanResult {
	sema <- struct{}{}        // acquire token
	defer func() { <-sema }() // release token
	defer wg.Done()

	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%v:%v", host, port), time.Millisecond*time.Duration(*timeout))
	result := scanResult{
		Port:    port,
		Success: err == nil,
	}
	runtime.Gosched()
	if conn != nil {
		conn.Close()
	}
	if result.Success == true {
		fmt.Println(host, result.Port, "open")
	} else if *verbose == true {
		fmt.Println(host, result.Port, "closed")
	}

	return &result
}
