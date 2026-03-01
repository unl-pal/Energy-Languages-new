JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := fannkuchredux
SRC := $(CLASS).java
N ?= 12

.PHONY: compile test run clean measure mem valgrind

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

run: compile
	$(JAVA) -cp . $(CLASS) $(N)

test: compile
	$(PYTEST) -q test_fannkuchredux_java.py

measure: compile
	sudo modprobe msr
	sudo ../../RAPL/main "$(JAVA) -cp . $(CLASS) $(N)" Java fannkuch-redux

mem: compile
	/usr/bin/time -v $(JAVA) -cp . $(CLASS) $(N)

valgrind: compile
	valgrind --tool=massif --stacks=yes $(JAVA) -cp . $(CLASS) $(N)

clean:
	rm -f $(CLASS).class
