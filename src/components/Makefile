BASEOBJ = so/base.so
REPLAYOBJ = so/replay.so

all: base replay

base: base.c
	gcc -Wall -fPIC -shared -lsyscall_intercept -o $(BASEOBJ) base.c -ldl

replay: replay.c
	gcc -Wall -fPIC -shared -o $(REPLAYOBJ) replay.c -ldl

testa: test/test.c
	gcc -Wall test/test.c
	LD_PRELOAD=${BASEOBJ} ./a.out test/test.txt

testu: test/test.c
	gcc -Wall test/test.c
	LD_PRELOAD=${BASEOBJ} ./a.out /dev/urandom

clean:
	rm $(BASEOBJ) $(REPLAYOBJ) test/a.out