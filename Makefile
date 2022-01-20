TESTDIR=tests

.PHONY: install install-dev test clean all

resource:
	python create_resources.py

clean:
	rm -rf build

install:
	flit install

install-dev:
	flit install -s

test:
	pytest $(TESTDIR)

all: clean resource test
