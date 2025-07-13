# Makefile for DFS Optimizer Project
.PHONY: help install format lint fix test clean check run all

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '$(BLUE)DFS Optimizer Makefile$(NC)'
	@echo '===================='
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install black isort autoflake flake8 pre-commit pytest pytest-cov
	pre-commit install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@echo "  Running isort..."
	@isort . --quiet
	@echo "  Running black..."
	@black . --quiet
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Run flake8 linter
	@echo "$(BLUE)Running linter...$(NC)"
	@flake8 . --max-line-length=100 --ignore=E203,E501,W503 --exclude=.git,__pycache__,old,build,dist,venv,.venv,backup_* || echo "$(YELLOW)⚠ Some linting issues found$(NC)"

lint-report: ## Generate detailed lint report
	@echo "$(BLUE)Generating lint report...$(NC)"
	@flake8 . --max-line-length=100 --ignore=E203,E501,W503 --exclude=.git,__pycache__,old,build,dist,venv,.venv,backup_* --output-file=lint-report.txt --tee
	@echo "$(GREEN)✓ Report saved to lint-report.txt$(NC)"

fix: ## Auto-fix common issues (unused imports, variables)
	@echo "$(BLUE)Auto-fixing issues...$(NC)"
	@echo "  Removing unused imports and variables..."
	@autoflake --remove-all-unused-imports --remove-unused-variables --recursive --in-place . --exclude=venv,.venv,backup_*
	@echo "  Fixing bare except statements..."
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./backup_*" -exec sed -i 's/except:/except Exception:/g' {} + 2>/dev/null || true
	@echo "  Running formatters..."
	@make format
	@echo "$(GREEN)✓ Auto-fixes applied$(NC)"

test: ## Run tests and system check
	@echo "$(BLUE)Running tests...$(NC)"
	@python check_system.py
	@if [ -d "tests" ] && [ -n "$$(find tests -name 'test_*.py' 2>/dev/null)" ]; then \
		echo "  Running pytest..."; \
		pytest tests/ -v --tb=short; \
	else \
		echo "$(YELLOW)⚠ No test files found in tests/$(NC)"; \
	fi

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@if [ -d "tests" ] && [ -n "$$(find tests -name 'test_*.py' 2>/dev/null)" ]; then \
		pytest tests/ --cov=. --cov-report=html --cov-report=term-missing; \
		echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"; \
	else \
		echo "$(YELLOW)⚠ No test files found$(NC)"; \
	fi

clean: ## Clean cache and temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf lint-report.txt 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

check: ## Run all checks (format, lint, test)
	@echo "$(BLUE)Running all checks...$(NC)"
	@make format
	@make lint
	@make test
	@echo "$(GREEN)✓ All checks complete$(NC)"

check-strict: ## Run strict checks (will fail on any issue)
	@echo "$(BLUE)Running strict checks...$(NC)"
	@black . --check
	@isort . --check-only
	@flake8 . --max-line-length=100 --ignore=E203,E501,W503 --exclude=.git,__pycache__,old,build,dist,venv,.venv,backup_*
	@make test

run: ## Run the DFS optimizer GUI
	@echo "$(BLUE)Starting DFS Optimizer GUI...$(NC)"
	@python enhanced_dfs_gui.py

run-cli: ## Run the optimizer in CLI mode
	@echo "$(BLUE)Starting DFS Optimizer CLI...$(NC)"
	@if [ -z "$(CSV)" ]; then \
		echo "$(RED)Error: Please specify CSV file with CSV=yourfile.csv$(NC)"; \
		echo "Usage: make run-cli CSV=path/to/draftkings.csv"; \
	else \
		python script.py $(CSV); \
	fi

pre-commit: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit...$(NC)"
	@pre-commit run --all-files || echo "$(YELLOW)⚠ Pre-commit made some changes$(NC)"

update: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@pip install --upgrade pip
	@pip install --upgrade -r requirements.txt
	@pip install --upgrade black isort autoflake flake8 pre-commit pytest pytest-cov
	@pre-commit autoupdate
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

dev: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@make install
	@make fix
	@make check
	@echo "$(GREEN)✓ Development environment ready$(NC)"

all: fix check ## Fix issues and run all checks
	@echo "$(GREEN)✓ All tasks complete$(NC)"

# Special targets for specific fixes
fix-imports: ## Fix only import issues
	@echo "$(BLUE)Fixing imports...$(NC)"
	@autoflake --remove-all-unused-imports --recursive --in-place . --exclude=venv,.venv,backup_*
	@isort .
	@echo "$(GREEN)✓ Imports fixed$(NC)"

fix-variables: ## Fix only unused variables
	@echo "$(BLUE)Fixing unused variables...$(NC)"
	@autoflake --remove-unused-variables --recursive --in-place . --exclude=venv,.venv,backup_*
	@echo "$(GREEN)✓ Variables fixed$(NC)"

stats: ## Show code statistics
	@echo "$(BLUE)Code Statistics:$(NC)"
	@echo "  Python files: $$(find . -name '*.py' -not -path './venv/*' -not -path './.venv/*' -not -path './backup_*' | wc -l)"
	@echo "  Total lines: $$(find . -name '*.py' -not -path './venv/*' -not -path './.venv/*' -not -path './backup_*' -exec wc -l {} + | tail -1 | awk '{print $$1}')"
	@echo "  TODO items: $$(grep -r 'TODO' --include='*.py' . 2>/dev/null | wc -l)"
	@echo "  FIXME items: $$(grep -r 'FIXME' --include='*.py' . 2>/dev/null | wc -l)"
