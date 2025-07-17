.PHONY: help install install-dev test test-cov lint format clean build docs

# Default target
help:
	@echo "CryptoTaxCalc Development Commands"
	@echo "=================================="
	@echo "install      - Install production dependencies"
	@echo "install-dev  - Install development dependencies"
	@echo "test         - Run tests"
	@echo "test-cov     - Run tests with coverage"
	@echo "lint         - Run linting (flake8, mypy)"
	@echo "format       - Format code (black, isort)"
	@echo "clean        - Clean build artifacts"
	@echo "build        - Build package"
	@echo "docs         - Build documentation"
	@echo "check        - Run all checks (format, lint, test)"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/

test-cov:
	pytest tests/ --cov=cryptotaxcalc --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 cryptotaxcalc/ tests/
	mypy cryptotaxcalc/

format:
	black cryptotaxcalc/ tests/
	isort cryptotaxcalc/ tests/

# Build and documentation
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

docs:
	cd docs && make html

# Combined checks
check: format lint test

# Development helpers
run:
	python -m cryptotaxcalc

shell:
	python -c "import cryptotaxcalc; print('CryptoTaxCalc imported successfully')"

# Database helpers
db-init:
	python -c "from cryptotaxcalc.database import init_db; init_db()"

db-clean:
	rm -f *.db *.sqlite *.sqlite3

# Sample data
sample-data:
	@echo "Creating sample data directory..."
	mkdir -p data/samples
	@echo "Sample data directory created at data/samples/"

# Security check
security-check:
	bandit -r cryptotaxcalc/
	safety check

# Performance
profile:
	python -m cProfile -o profile.stats -m cryptotaxcalc

# Docker helpers (if needed later)
docker-build:
	docker build -t cryptotaxcalc .

docker-run:
	docker run -it --rm cryptotaxcalc

# Git helpers
git-hooks:
	@echo "Setting up git hooks..."
	@if [ -d .git ]; then \
		echo "#!/bin/sh" > .git/hooks/pre-commit; \
		echo "make check" >> .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "Git hooks installed"; \
	else \
		echo "Not a git repository"; \
	fi 