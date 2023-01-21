CC=g++
CFLAGS=-std=c++11

do: main.cpp strength.o pokerlib/pokerlib.o
	${CC} ${CFLAGS} main.cpp pokerlib/pokerlib.o strength.o -o do

strength.o: strength.cpp strength.h
	${CC} -c ${CFLAGS} strength.cpp -o strength.o

pokerlib/pokerlib.o: pokerlib/pokerlib.c pokerlib/arrays.h
	${CC} -c ${CFLAGS} pokerlib/pokerlib.c -o pokerlib/pokerlib.o

clean:
	rm -f do pokerlib/pokerlib.o strength.o
