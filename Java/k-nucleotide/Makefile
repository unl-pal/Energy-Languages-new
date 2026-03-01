JAVAC ?= javac
JAVA  ?= java
PYTEST ?= pytest

CLASS := knucleotide
SRC := $(CLASS).java

# override on command line if needed
FASTUTIL_JAR ?= /usr/share/java/fastutil.jar
CP := .:$(FASTUTIL_JAR)

N ?= 1000000000

.PHONY: compile test run clean

$(CLASS).class: $(SRC)
	$(JAVAC) -d . -cp $(CP) $(SRC)

compile: $(CLASS).class

test: compile
	FASTUTIL_JAR=$(FASTUTIL_JAR) LONG_REPEATS=$(N) LONG_ROUNDS=3 $(PYTEST) -q test_knucleotide_java.py

run: compile
	$(JAVA) -cp $(CP) $(CLASS) 0 < knucleotide-input25000000.txt

clean:
	rm -f $(CLASS).class
