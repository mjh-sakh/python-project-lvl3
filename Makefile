#Makefile

install:
	poetry install

build:
	poetry build

publish:
	poetry publish --dry-run

lint:
	poetry run flake8 page_loader

reps:
	poetry show --tree

run:


run_help:


test:
	poetry run mypy page_loader
	poetry run pytest

coverage:
	poetry run coverage run -m pytest
	poetry run coverage xml

package-install:
	pip3 install --force-reinstall dist/hexlet_code-0.1.0-py3-none-any.whl