BASEOBJ = read.so
REPLAYOBJ = 

all: base replay

base:
	gcc -Wall -fPIC -shared -o $(BASEOBJ) read.c -ldl

replay:
	# gcc -Wall -fPIC -shared -o $(REPLAYOBJ) read.c -ldl

clean:
	rm $(BASEOBJ) $(REPLAYOBJ)