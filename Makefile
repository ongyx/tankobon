MODULE=tankobon
DOCDIR=docs

.PHONY: clean doc

clean:
	rm -rf $(DOCDIR)/$(MODULE)

doc:
	pdoc -o $(DOCDIR) --html $(MODULE)

all: clean doc
