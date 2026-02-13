include common.mk

# Our directories
API_DIR = server
DB_DIR = data
SEC_DIR = security
REQ_DIR = .

# Export the Python path for the project
PYTHONPATH ?= $(shell pwd)
export PYTHONPATH

FORCE:

prod: all_tests github

dev:
	sudo systemctl start mongod
	. ./venv/bin/activate && . ./local.sh

github: FORCE
	- git commit -a
	git push origin master

all_tests: FORCE
	cd $(API_DIR); make tests
	cd $(DB_DIR); make tests

dev_env: FORCE
	pip install -r $(REQ_DIR)/requirements-dev.txt
	@echo "You should set PYTHONPATH to: "
	@echo $(shell pwd)

prod_env: FORCE
	pip install -r $(REQ_DIR)/requirements.txt

docs: FORCE
	cd $(API_DIR); make docs
