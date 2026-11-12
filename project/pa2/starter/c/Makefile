# CSC 4200/5200 PA2 -- C starter Makefile
# make build      compile ./etpt-send and ./etpt-recv
# make check      run the course self-check against this repository
# make measure    run the measurement sweep for your profile (10 to 15 minutes)
# make clean      remove build output

CFLAGS   ?= -std=c11 -Wall -Wextra -Wpedantic -O2 -g
CPPFLAGS += -D_DEFAULT_SOURCE -Iinclude
LDLIBS   += -lm
PA2      ?= $(HOME)/csc4200-course/project/pa2

COMMON  = src/etpt.c src/transport_etpt.c
HEADERS = include/etpt.h include/transport.h

.PHONY: build check measure clean

build: etpt-send etpt-recv

etpt-send: src/etpt_send.c $(COMMON) $(HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ src/etpt_send.c $(COMMON) $(LDLIBS)

etpt-recv: src/etpt_recv.c $(COMMON) $(HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ src/etpt_recv.c $(COMMON) $(LDLIBS)

check: build
	python3 $(PA2)/etpt_selfcheck.py --no-build || true

measure: build
	python3 $(PA2)/etpt_measure.py

clean:
	rm -f etpt-send etpt-recv
