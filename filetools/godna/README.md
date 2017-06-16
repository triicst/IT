# Godna DNA generator

Godna is a storage benchmarking tool that generates a random DNA sequence and writes it concurently to multiple files.  

## Usage

```
./godna [-n <number of files>  -t <cpu threads> -c <concurrecy> -d </dir/path>] -s <size in bytes>
```

## Arguments

```
  -c int
    	Optional: set number of concurrent file writers to use; defaults to the number of logical CPUs in your system
  -d string
    	Optional: Directory to write the files; defaults to the current directory
  -n int
    	Optional: set the number of files; defaults to 1 file 
  -s int
    	Required: the size of the file(s) to generate in Bytes
  -t int
    	Optional: set number CPU threads available for use; defaults to the number of logical CPUs in your system
```

## Example

```
./godna -n 1024 -t 16 -c 32 -s 10485760 -d /tmp
```
