package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"sync"
	"runtime"
	"time"
)

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())
	size := 1024 * 1024 * 10 
        wg := new(sync.WaitGroup)
        sema := make(chan struct{}, runtime.NumCPU())
	out := genstring(size)

        for x := 1; x <= 5120; x++ {
                wg.Add(1)
                go spraydna(x, wg, sema, &out)
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

func spraydna(count int, wg *sync.WaitGroup, sema chan struct{}, out *[]byte) {
        defer wg.Done()
        sema <- struct{}{}        // acquire token
        defer func() { <-sema }() // release token
	filename := fmt.Sprintf("dna/dna-%d.txt", count)
	f, err := os.Create(filename)
        check(err)
	defer f.Close()
	
	w := bufio.NewWriter(f)
    	w.Write(*out)
    	//fmt.Printf("wrote %d bytes\n", o)
	w.Flush()
}
