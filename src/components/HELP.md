# Resources

https://catonmat.net/simple-ld-preload-tutorial-part-two

## Compilation
gcc -Wall -fPIC -shared -o read.so read.c -ldl

LD_PRELOAD=so/base.so ./a.out test.txt
LD_PRELOAD=so/base.so ./a.out /dev/urandom