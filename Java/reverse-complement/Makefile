JAVA ?= java
JAVAC ?= javac
PYTEST ?= pytest
CLASS := revcomp
TEST_FILE := test_revcomp_java.py

.PHONY: all compile run test clean

all: compile

compile:
	$(JAVAC) $(CLASS).java

run: compile
	$(JAVA) -cp . $(CLASS) 0

test: compile
	$(PYTEST) -q $(TEST_FILE)

clean:
	rm -f $(CLASS)*.class
