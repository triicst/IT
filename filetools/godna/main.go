package main

import (
	"bufio"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"sync"
	"time"
)

func main() {

	// define and set default command parameter flags
	var nFlag = flag.Int("n", 1, "Optional: set the number of files; defaults to 1 file")
	var tFlag = flag.Int("t", runtime.NumCPU(), "Optional: set number CPU threads available for use; defaults to the number of logical CPUs in your system")
	var cFlag = flag.Int("c", runtime.NumCPU(), "Optional: set number of concurrent file writers to use; defaults to the number of logical CPUs in your system")
	var sFlag = flag.Int("s", 0, "Required: the size of the file(s) to generate in Bytes")
	var dFlag = flag.String("d", ".", "Optional: Directory to write the files; defaults to the current directory")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "\nUsage: %s [-n <number of files>  -t <cpu threads> -c <concurrency> -d </dir/path>] -s <size in bytes>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "\nExample: %s -n 1024 -t 16 -c 32 -s 10485760 -d /tmp\n\n", os.Args[0])
		flag.PrintDefaults()
		fmt.Println()
	}
	flag.Parse()

	if *sFlag == 0 {
		fmt.Fprintf(os.Stderr, "\nMissing required -s (size) argument\n\n")
		flag.Usage()
		os.Exit(2)
	}

	runtime.GOMAXPROCS(*tFlag)
	size := *sFlag
	wg := new(sync.WaitGroup)
	sema := make(chan struct{}, *cFlag)
	out := genstring(size)

	for x := 1; x <= *nFlag; x++ {
		wg.Add(1)
		go spraydna(x, wg, sema, &out, *dFlag)
	}
	wg.Wait()
}

func genstring(size int) []byte {
	//r := rand.New(rand.NewSource(time.Now().UnixNano()))
	rand.Seed(time.Now().UnixNano())
	dnachars := []byte("GATC")
	dna := make([]byte, 0)
	for x := 0; x < size; x++ {
		dna = append(dna, dnachars[rand.Intn(len(dnachars))])
	}
	return dna
}

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func spraydna(count int, wg *sync.WaitGroup, sema chan struct{}, out *[]byte, dir string) {
	defer wg.Done()
	sema <- struct{}{}        // acquire token
	defer func() { <-sema }() // release token
	filename := fmt.Sprintf("%s/dna-%d.txt", dir, count)
	f, err := os.Create(filename)
	check(err)
	defer f.Close()

	w := bufio.NewWriter(f)
	w.Write(*out)
	//fmt.Printf("wrote %d bytes\n", o)
	w.Flush()
}
