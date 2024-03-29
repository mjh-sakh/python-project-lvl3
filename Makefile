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

test:
	poetry run mypy page_loader
	poetry run coverage run -m pytest

coverage:
	poetry run coverage xml

package-install:
	pip3 install --force-reinstall dist/hexlet_code-0.1.0-py3-none-any.whl