JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := nbody
SRC := $(CLASS).java

# Used by test runtime too
N ?= 50000000

.PHONY: compile test run clean measure mem valgrind

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

# correctness via constant python test
test: compile
	LONG_N=$(N) $(PYTEST) -q test_nbody_java.py

# benchmark-style run
run: compile
	$(JAVA) -cp . $(CLASS) $(N)

measure: compile
	sudo modprobe msr
	sudo ../../RAPL/main "$(JAVA) -cp . $(CLASS) 50000000" Java n-body

mem: compile
	/usr/bin/time -v $(JAVA) -cp . $(CLASS) 50000000

valgrind: compile
	valgrind --tool=massif --stacks=yes $(JAVA) -cp . $(CLASS) 50000000

clean:
	rm -f $(CLASS).classJAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := nbody
SRC := $(CLASS).java

# Used by test runtime too
N ?= 500000

.PHONY: compile test run clean measure mem valgrind

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

# correctness via constant python test
test: compile
	LONG_N=$(N) $(PYTEST) -q test_nbody_java.py

# benchmark-style run
run: compile
	$(JAVA) -cp . $(CLASS) $(N)

measure: compile
	sudo modprobe msr
	sudo ../../RAPL/main "$(JAVA) -cp . $(CLASS) 50000000" Java n-body

mem: compile
	/usr/bin/time -v $(JAVA) -cp . $(CLASS) 50000000

valgrind: compile
	valgrind --tool=massif --stacks=yes $(JAVA) -cp . $(CLASS) 50000000

clean:
	rm -f $(CLASS).class
