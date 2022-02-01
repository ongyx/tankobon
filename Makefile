MODULE=tankobon
DOCDIR=docs
LOGO=./docs/logo.jpg

.PHONY: clean doc

clean:
	rm -rf $(DOCDIR)/$(MODULE)

doc:
	pdoc -o $(DOCDIR) --logo '/logo.jpg' --docformat google '$(MODULE)' '!$(MODULE).ui'

all: clean doc
