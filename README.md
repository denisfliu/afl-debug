# AFL++ Debug
Trying to automate debugging using the partial replayability I've written for AFL++.

TODO: formatter

## AFL++ Benchmark
Currently using 3 test binaries: Xpdf, sleep, and objdump

Xpdf: (mostly following this tutorial https://github.com/antonio-morales/Fuzzing101/tree/main/Exercise%201)
 - Download: wget https://dl.xpdfreader.com/old/xpdf-3.02.tar.gz
 - Compile:
   - CC=/AFLplusplus/afl-clang-fast CXX=/AFLplusplus/afl-clang-fast++ ./configure
   - make
   - make install

Sleep
 - GNU coreutils; follow https://github.com/coreutils/coreutils/blob/master/README-hacking
 - Download: git clone https://git.savannah.gnu.org/git/coreutils
 - Compile: 
   - CC=afl-clang-lto ./configure 
   - make
   - make install

Objdump
 - GNU binutils
 - Download: https://ftp.gnu.org/gnu/binutils/binutils-2.41.tar.gz
 - Compile:	
   - CC=afl-clang-lto ./configure
   - make
   - make install
