JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := regexredux
SRC := $(CLASS).java

# Used by test runtime too
N ?= 8000000

.PHONY: compile test run clean measure mem valgrind restore

# Recompile current optimized source when it changes
$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

# correctness via constant python test
test: compile
	LONG_REPEATS=$(N) $(PYTEST) -q test_regexredux_java.py

# benchmark-style run
run: compile
	$(JAVA) -cp . $(CLASS) 0 < ../../regexredux-input5000000.txt

measure: compile
	sudo modprobe msr
	sudo ../../RAPL/main "$(JAVA) -cp . $(CLASS) 0 < ../../regexredux-input5000000.txt" Java regex-redux

mem: compile
	/usr/bin/time -v $(JAVA) -cp . $(CLASS) 0 < ../../regexredux-input5000000.txt

valgrind: compile
	valgrind --tool=massif --stacks=yes $(JAVA) -cp . $(CLASS) 0 < ../../regexredux-input5000000.txt

clean:
	rm -f $(CLASS).class
