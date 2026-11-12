# CSC 4200/5200 PA2 -- Python starter Makefile
# make build      check syntax and make the launchers executable
# make check      run the course self-check against this repository
# make measure    run the measurement sweep for your profile (10 to 15 minutes)
# make clean      remove build output

PY       ?= python3
PA2      ?= $(HOME)/csc4200-course/project/pa2

.PHONY: build check measure clean

build:
	chmod +x etpt-send etpt-recv
	$(PY) -m py_compile src/*.py

check: build
	$(PY) $(PA2)/etpt_selfcheck.py --no-build || true

measure: build
	$(PY) $(PA2)/etpt_measure.py

clean:
	rm -rf src/__pycache__
