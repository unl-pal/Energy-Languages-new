JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := pidigits
SRC := $(CLASS).java
N ?= 40000

# Path containing libjgmplib.so
JGMPLIB_DIR ?= /home/fatemeh/Desktop/copy/energybench/Energy-Languages/Java/pidigits

# Path containing libgmp.so
GMP_DIR ?= /home/fatemeh/Energy-Languages/Java/pidigits

JAVA_OPTS ?= -Djava.library.path=$(JGMPLIB_DIR)

.PHONY: compile test run clean

$(CLASS).class: $(SRC)
	$(JAVAC) -d . $(SRC)

compile: $(CLASS).class

run: compile
	LD_LIBRARY_PATH=$(GMP_DIR):$$LD_LIBRARY_PATH $(JAVA) $(JAVA_OPTS) -cp . $(CLASS) $(N)

test: compile
	JAVA_OPTS="$(JAVA_OPTS)" LD_LIBRARY_PATH="$(GMP_DIR):$$LD_LIBRARY_PATH" LONG_N=$(N) $(PYTEST) -q test_pidigits_java.py

clean:
	rm -f $(CLASS).class
