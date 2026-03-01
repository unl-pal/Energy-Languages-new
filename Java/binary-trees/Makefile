JAVAC ?= javac
JAVA_RELEASE ?= 17
JAVACFLAGS ?= --release $(JAVA_RELEASE)
JAVA  ?= java
PYTEST ?= pytest

CLASS := binarytrees
SRC := $(CLASS).java
N ?= 21

.PHONY: compile test run clean

$(CLASS).class: $(SRC)
	$(JAVAC) $(JAVACFLAGS) -d . $(SRC)

compile: $(CLASS).class

run: compile
	$(JAVA) -cp . $(CLASS) $(N)

test: compile
	$(PYTEST) -q test_binarytrees_java.py

clean:
	rm -f $(CLASS).class
