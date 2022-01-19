MODULE=tankobon
DOCDIR=docs
TESTDIR=tests

.PHONY: install install-dev test doc clean all

resource:
	python create_resources.py

clean:
	rm -rf build docs

doc:
	pdoc --html --output-dir $(DOCDIR) $(MODULE)

install:
	flit install

install-dev:
	flit install -s

test:
	pytest $(TESTDIR)

all: clean resource doc test
