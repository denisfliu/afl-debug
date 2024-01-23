COMPONENTS = src/components/

BASEOBJ = $(COMPONENTS)so/base.so
REPLAYOBJ = $(COMPONENTS)so/replay.so
BASEC = $(COMPONENTS)base.c
REPLAYC = $(COMPONENTS)replay.c
TESTC = $(COMPONENTS)test/replay.c
OUT = $(COMPONENTS)a.out

all: base replay

base: $(BASEC)
	gcc $(BASEC) -lsyscall_intercept -fPIC -Wall -shared -ldl -o $(BASEOBJ)

replay: $(REPLAYC)
	gcc $(REPLAYC) -lsyscall_intercept -fPIC -Wall -shared -ldl -o $(REPLAYOBJ)

testa: $(TESTC)
	gcc -Wall $(TESTC) -o $(OUT)
	LD_PRELOAD=${BASEOBJ} $(OUT) $(COMPONENTS)test/test.txt

testu: $(TESTC)
	gcc -Wall $(TESTC) -o $(OUT)
	LD_PRELOAD=${BASEOBJ} $(OUT) /dev/urandom

clean:
	rm $(BASEOBJ) $(REPLAYOBJ) $(COMPONENTS)test/a.out