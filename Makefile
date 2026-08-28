.PHONY: install test lint typecheck run sample
install:
	python -m pip install -e ".[dev]"
test:
	pytest
lint:
	ruff check .
typecheck:
	mypy
run:
	uvicorn redsentinel.app:app --reload
sample:
	redsentinel scan --authorized --output reports/sample
