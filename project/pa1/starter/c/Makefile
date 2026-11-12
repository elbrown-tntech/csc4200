# CSC 4200/5200 PA1 -- C starter Makefile
# make build        compile ./etp-server and ./etp-client
# make run-server   run the server on PORT (default 5000) serving ROOT
# make check        run the course self-check against this repository
# make clean        remove build output

CFLAGS   ?= -std=c11 -Wall -Wextra -Wpedantic -O2 -g
CPPFLAGS += -D_DEFAULT_SOURCE -Iinclude
LDLIBS   += -pthread -lcrypto
PORT     ?= 5000
ROOT     ?= server-files
SELFCHECK ?= $(HOME)/csc4200-course/project/etp_selfcheck.py

COMMON  = src/etp.c src/transport_tcp.c
HEADERS = include/etp.h include/transport.h

.PHONY: build run-server check clean

build: etp-server etp-client

etp-server: src/server.c $(COMMON) $(HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -pthread -o $@ src/server.c $(COMMON) $(LDLIBS)

etp-client: src/client.c $(COMMON) $(HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ src/client.c $(COMMON) $(LDLIBS)

run-server: build
	mkdir -p $(ROOT)
	./etp-server --port $(PORT) --root $(ROOT)

check: build
	python3 $(SELFCHECK) --no-build || true

clean:
	rm -f etp-server etp-client
