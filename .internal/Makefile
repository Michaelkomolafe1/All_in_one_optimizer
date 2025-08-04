# DFS Optimizer Makefile

.PHONY: help install test clean run gui cli backup

help:
	@echo "DFS Optimizer - Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make clean     - Clean cache and temp files"
	@echo "  make run       - Run the optimizer (GUI)"
	@echo "  make gui       - Run GUI interface"
	@echo "  make cli       - Run CLI interface"
	@echo "  make backup    - Create project backup"

install:
	pip install -r requirements.txt

test:
	python test_integration.py
	python test.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

run: gui

gui:
	python launch_dfs_optimizer.py --gui

cli:
	python launch_dfs_optimizer.py --cli

backup:
	@echo "Creating backup..."
	@mkdir -p ../backups
	@tar -czf ../backups/dfs_optimizer_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude='*.pyc' \
		--exclude='__pycache__' \
		--exclude='.venv' \
		--exclude='venv' \
		--exclude='.git' \
		--exclude='*.log' \
		.
	@echo "Backup created in ../backups/"

format:
	black .
	isort .

lint:
	flake8 . --max-line-length=100 --exclude=.venv,venv,__pycache__

pre-commit:
	pre-commit run --all-files
