BASEOBJ = base.so
REPLAYOBJ = replay.so

all: base replay

base:
	gcc -Wall -fPIC -shared -o $(BASEOBJ) base.c -ldl

replay:
	# gcc -Wall -fPIC -shared -o $(REPLAYOBJ) replay.c -ldl

clean:
	rm $(BASEOBJ) $(REPLAYOBJ)