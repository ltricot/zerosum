
CC=gcc
CFLAGS=-Ofast

allfive: allfive.c pokerlib.o
	${CC} ${CFLAGS} allfive.c pokerlib.o -s -o allfive

pokerlib.o: pokerlib.c arrays.h
	${CC} -c ${CFLAGS} pokerlib.c -o pokerlib.o

clean:
	rm -f allfive pokerlib.o
