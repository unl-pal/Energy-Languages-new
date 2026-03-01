JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := mandelbrot
SRC := $(CLASS).java

# This controls test runtime too
N ?= 20000

.PHONY: compile test run clean measure mem valgrind

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

# correctness via constant python test
test: compile
	LONG_N=$(N) $(PYTEST) -q test_mandelbrot_java.py

# benchmark-style run
run: compile
	$(JAVA) -cp . $(CLASS) $(N)

measure: compile
	sudo modprobe msr
	sudo ../../RAPL/main "$(JAVA) -cp . $(CLASS) 16000" Java mandelbrot

mem: compile
	/usr/bin/time -v $(JAVA) -cp . $(CLASS) 16000

valgrind: compile
	valgrind --tool=massif --stacks=yes $(JAVA) -cp . $(CLASS) 16000

clean:
	rm -f $(CLASS).class
