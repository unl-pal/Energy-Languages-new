JAVAC ?= javac
JAVA ?= java
PYTEST ?= pytest -q

CLASS = spectralnorm
SRC = $(CLASS).java
TEST = test_$(CLASS)_java.py

SPECTRAL_N ?= 1000
SPECTRAL_N_LONG ?= 800
SPECTRAL_TOL ?= 5e-9

.PHONY: compile run test test-long clean

compile:
	$(JAVAC) $(SRC)

run: compile
	$(JAVA) -cp . $(CLASS) $(SPECTRAL_N)

test: compile
	SPECTRAL_N=$(SPECTRAL_N) SPECTRAL_TOL=$(SPECTRAL_TOL) $(PYTEST) $(TEST)

test-long: compile
	SPECTRAL_N=$(SPECTRAL_N_LONG) SPECTRAL_TOL=$(SPECTRAL_TOL) $(PYTEST) $(TEST)

clean:
	rm -f $(CLASS).class $(CLASS)\$$Approximate.class __pycache__/*.pyc .pytest_cache -r
