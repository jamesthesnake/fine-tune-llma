SHELL := /bin/bash
PYTHON:=python3
PIP:=pip
SOURCEDIR:=./hrd_models
TESTS:=${SOURCEDIR}/tests/
VERSION_MODULE:=${SOURCEDIR}/version.py
VERSION := $(shell ${PYTHON} ${VERSION_MODULE})
NEXUS_URL = https://nexus.opstempus.com/repository/pypi-internal/

pyenv: # Installs pyenv if not already installed
ifeq ($(shell command -v pyenv 2> /dev/null), )
	@echo "--- Installing pyenv ---"
	curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
	export PYENV_ROOT="$HOME/.pyenv"
	export PATH="$PYENV_ROOT/bin:$PATH"
else
	@echo "--- Pyenv already installed ---";
endif
	@echo "--- Installing Python ---"
	pyenv install --skip-existing 3.8.5
	pyenv local 3.8.5

poetry: # Installs poetry if it is not already installed
ifeq ($(shell command -v poetry 2> /dev/null),)
	@echo "--- Installing poetry ---"
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | $(PYTHON) -
else
	@echo "--- Poetry already installed ---";
endif

init: pyenv poetry # Runs initial setup for the repo
	@echo "--- Initializing project environment ---"

build: init install
	poetry build

clean: clean-build clean-pyc clean-test # remove all build, test, coverage and Python artifacts

clean-build: # remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: # remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: # remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

format: # check code formatting with black
	$(PYTHON) -m black --check --diff ${SOURCEDIR}

format-inplace: # check and fix code formatting with black
	$(PYTHON) -m black --line-length 100 ${SOURCEDIR}

lint: # check style with flake8
	$(PYTHON) -m flake8 --max-line-length 101 ${SOURCEDIR}

test-no-etl: install  # Run tests, excluding ETL; config picked up from pyproject.toml
	poetry run pytest --cov

test-etl: install-etl  # Run only ETL tests (slow)
	$(PYTHON) -m poetry run dotenv run pytest -s -W ignore hrd_models/tests/tests_etl

test-train: install-train  # Run only RNA training tests
	$(PYTHON) -m poetry run dotenv run pytest -s -W ignore hrd_models/tests/tests_train

test-dna: #  # Run only DNA tests (for faster development)
	$(PYTHON) -m poetry run pytest -s -W ignore hrd_models/tests/tests_dna_predictor

test-rna: #  # Run only RNA tests (for faster development)
	$(PYTHON) -m poetry run pytest -s -W ignore hrd_models/tests/tests_rna_predictor

test-orders: # Get test orders
	$(PYTHON) -m poetry run dotenv run python hrd_models/tests/tests_common/test_orders.py

test: test-no-etl  # this gets run on CI and we don't want ETL tests there

install: clean init
	poetry install

install-etl: clean init
	$(PYTHON) -m poetry install --extras "etl"

install-train: clean init
	$(PYTHON) -m poetry install --extras "train"

# etl requires system binaries
# on tacos, `sudo yum install python3-devel snappy-devel gcc-c++`

etl: install-etl
	$(PYTHON) -m poetry run dotenv run python hrd_models/etl/main.py

train: install-train
	$(PYTHON) -m poetry run dotenv run python hrd_models/train/main.py

backfill: install-etl
	$(PYTHON) -m poetry run dotenv run python validation/backfill.py

publish: build  # Upload package to nexus
	$(eval IS_ALPHA := $(shell poetry version | grep -c alpha))
	@echo GIT_BRANCH: $(GIT_BRANCH)
	@echo IS_ALPHA: $(IS_ALPHA)
	@if [[ $(GIT_BRANCH) == main ]]; then \
		echo "Publishing to Nexus from main"; \
		poetry config repositories.nexus "${NEXUS_URL}"; \
		poetry publish --repository nexus --username "${NEXUS_USERNAME}" --password "${NEXUS_PASSWORD}"; \
	elif [[ ($(GIT_BRANCH) == develop) && ($(IS_ALPHA) == 1) ]]; then \
		echo "Publishing alpha version to Nexus from develop"; \
		poetry config repositories.nexus "${NEXUS_URL}"; \
		poetry publish --repository nexus --username "${NEXUS_USERNAME}" --password "${NEXUS_PASSWORD}"; \
	else \
		echo "Non-main, non-alpha-release branch detected, halting publishing"; \
	fi
