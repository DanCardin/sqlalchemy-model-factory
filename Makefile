.PHONY: lock install build test lint format publish
.DEFAULT_GOAL := help

lock:
	poetry lock

install:
	poetry install

build:
	poetry build

test:
	coverage run -m py.test src tests -vv
	coverage combine --append
	coverage report
	coverage xml

lint:
	flake8 src tests
	isort --check-only src tests
	pydocstyle src tests
	mypy src tests
	black --check src tests

format:
	isort --quiet src tests
	black src tests

publish: build
	poetry publish -u __token__ -p '${PYPI_PASSWORD}' --no-interaction
