# common make vars and targets:
export LINTER = flake8
export PYLINTFLAGS = --exclude=__main__.py

export CLOUD_MONGO = 0

PYTHONFILES = $(shell ls *.py)
PYTESTFLAGS = -vv --verbose --cov-branch --cov-report term-missing --tb=short -W ignore::FutureWarning

MAIL_METHOD = api

FORCE:

tests: lint pytests

lint: $(patsubst %.py,%.pylint,$(PYTHONFILES))

%.pylint:
	@$(LINTER) $(PYLINTFLAGS) $*.py || echo "flake8 found style issues but just warning instead of failing"

pytests: FORCE
	pytest $(PYTESTFLAGS) --cov=$(PKG)

# test a python file:
%.py: FORCE
	@$(LINTER) $(PYLINTFLAGS) $@ || echo "flake8 found style issues but just warning instead of failing"
	pytest $(PYTESTFLAGS) tests/test_$*.py

nocrud:
	-rm *~
	-rm *.log
	-rm *.out
	-rm .*swp
	-rm $(TESTDIR)/*~
