# Godu
## A fast concurrent and parallel 'du' like utility written in Go.

Godu uses goroutines for concurrency and threads for parallelization. Each directory is proccessed concurently with it's own goroutine and by default godu will create as many threads as logical CPUs in your system. The threads will process the pool of concurent goroutines until done. With a large directory tree with many directories, there could be many thousands of lightweight goroutines running concurently.  

## Usage

```
Usage: bin/godu [-v, -t int] topdir1 topdirN

Example: bin/godu -v /home/rmcdermo /fh/fast/mcdermott_r /fh/secure/research/mcdermott_r

  -t int
        Optional: set number of threads, defaults to number of logical cores (default 56)
  -v    Optional: show verbose progress messages
```

## Binaries

Compiled binary versions of godu are available via the links below:

- [Linux x64](https://github.com/FredHutch/IT/raw/master/filetools/godu/bin/godu "https://github.com/FredHutch/IT/raw/master/filetools/godu/bin/godu")

- [Windows x64](https://github.com/FredHutch/IT/raw/master/filetools/godu/bin/godu.exe "https://github.com/FredHutch/IT/raw/master/filetools/godu/bin/godu.exe")
