# CSC 4200/5200 PA1 -- Python starter Makefile
# make build        check syntax and make the launchers executable
# make run-server   run the server on PORT (default 5000) serving ROOT
# make check        run the course self-check against this repository
# make clean        remove build output

PY       ?= python3
PORT     ?= 5000
ROOT     ?= server-files
SELFCHECK ?= $(HOME)/csc4200-course/project/etp_selfcheck.py

.PHONY: build run-server check clean

build:
	chmod +x etp-server etp-client
	$(PY) -m py_compile src/*.py

run-server: build
	mkdir -p $(ROOT)
	./etp-server --port $(PORT) --root $(ROOT)

check: build
	$(PY) $(SELFCHECK) --no-build || true

clean:
	rm -rf src/__pycache__
