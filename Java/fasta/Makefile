JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := fasta
SRC := $(CLASS).java
N ?= 30000000

.PHONY: compile test run clean

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

run: compile
	$(JAVA) -cp . $(CLASS) $(N)

test: compile
	LONG_N=$(N) $(PYTEST) -q test_fasta_java.py

clean:
	rm -f $(CLASS).class
