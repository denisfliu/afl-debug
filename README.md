# AFL++ Debug
Trying to automate debugging using the partial replayability I've written for AFL++.

TODO: Write LD_PRELOAD stuff. Write AFL++ launcher which can automatically load our LD_PRELOAD stuff. Should be able to be used from benchmark framework as well as in isolation.
TODO: make a makefile for components/
TODO: Cheese a way to initialize the seed to what we want

## AFL++ Benchmark
Currently using 3 test binaries: Xpdf (pdftotext), sleep, and objdump

Xpdf
 - Mostly following this tutorial https://github.com/antonio-morales/Fuzzing101/tree/main/Exercise%201
 - Download: wget https://dl.xpdfreader.com/old/xpdf-3.02.tar.gz
 - Compile:
```
CC=/AFLplusplus/afl-clang-fast CXX=/AFLplusplus/afl-clang-fast++ ./configure --prefix="$HOME/TestBinaries/fuzzing_xpdf/install"
make
make install
```
(`pdftotext` located in `install/bin` directory)


Sleep
 - GNU coreutils; follow https://github.com/coreutils/coreutils/blob/master/README-hacking
 - Download: git clone https://git.savannah.gnu.org/git/coreutils
 - Compile: 
```
./bootstrap
CC=/AFLplusplus/afl-clang-fast CXX=/AFLplusplus/afl-clang-fast++ ./configure --prefix="$HOME/TestBinaries/fuzzing_sleep/install"
make src/sleep
```
(`sleep` located in `src` directory)


Objdump
 - GNU binutils
 - Download: https://ftp.gnu.org/gnu/binutils/binutils-2.41.tar.gz
 - Compile:
```
CC=afl-clang-lto ./configure --prefix="$HOME/TestBinaries/fuzzing_objdump/install"
make
make install
```
(`objdump` located in `install/bin` directory)

### Running the benchmark
```
python -m run_bench -p [xpdf/sleep/objdump/custom_binary_path]
```

syscall_intercept Library: https://github.com/pmem/syscall_intercept
