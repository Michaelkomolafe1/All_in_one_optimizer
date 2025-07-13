#!/usr/bin/env python3
"""
DFS Optimizer Development Tools Runner
Automatically runs all code quality tools and tests
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Colors for output
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color
BOLD = "\033[1m"


def print_header(title):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{BOLD}{title.center(60)}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")


def print_section(title):
    """Print a section header"""
    print(f"\n{CYAN}▶ {title}{NC}")
    print(f"{CYAN}{'─' * 50}{NC}")


def run_command(cmd, description, show_output=True, check_success=True):
    """Run a command and return success status"""
    print(f"  {description}... ", end="", flush=True)

    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"{GREEN}✓{NC}")
            if show_output and result.stdout:
                print(f"{result.stdout}")
            return True
        else:
            if check_success:
                print(f"{RED}✗{NC}")
                if result.stderr:
                    print(f"{RED}Error: {result.stderr}{NC}")
            else:
                print(f"{YELLOW}⚠{NC}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error: {e}{NC}")
        return False


def main():
    """Main function to run all tools"""
    start_time = datetime.now()

    print_header("DFS OPTIMIZER TOOLS RUNNER")
    print(f"{CYAN}Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{NC}")

    # Check if in virtual environment
    if not hasattr(sys, "prefix"):
        print(f"{RED}❌ Not in virtual environment!{NC}")
        print(f"{YELLOW}Run: source .venv/bin/activate{NC}")
        sys.exit(1)

    # Menu options
    print(f"\n{BOLD}Choose what to run:{NC}")
    print("1. Quick Format (black + isort)")
    print("2. Full Code Check (format + lint + test)")
    print("3. Fix All Issues (auto-fix + format + check)")
    print("4. Code Analysis (stats + lint report)")
    print("5. Run Optimizer GUI")
    print("6. Run Everything (complete pipeline)")
    print("0. Exit")

    choice = input(f"\n{CYAN}Enter choice (0-6): {NC}").strip()

    if choice == "0":
        print("Exiting...")
        sys.exit(0)

    # Track results
    results = {}

    if choice in ["1", "2", "3", "6"]:
        print_section("Code Formatting")
        results["isort"] = run_command(["isort", "."], "Sorting imports")
        results["black"] = run_command(["black", "."], "Formatting with Black")

    if choice in ["2", "3", "4", "6"]:
        print_section("Code Quality Checks")

        if choice in ["3", "6"]:
            # Auto-fix first
            results["autoflake"] = run_command(
                [
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--remove-unused-variables",
                    "--recursive",
                    "--in-place",
                    ".",
                ],
                "Removing unused imports/variables",
            )

        # Run flake8
        lint_result = subprocess.run(
            [
                "flake8",
                ".",
                "--max-line-length=100",
                "--ignore=E203,E501,W503,F403,F405",
                "--exclude=.git,__pycache__,venv,.venv,backup_*",
                "--statistics",
            ],
            capture_output=True,
            text=True,
        )

        if lint_result.returncode == 0:
            print(f"  Running lint check... {GREEN}✓ No issues!{NC}")
            results["lint"] = True
        else:
            # Parse statistics
            stats_lines = [line for line in lint_result.stdout.split("\n") if line.strip()]
            issue_count = len(stats_lines)
            print(f"  Running lint check... {YELLOW}⚠ {issue_count} issues found{NC}")

            if choice in ["4", "6"]:
                # Show summary
                print(f"\n{YELLOW}Top issues:{NC}")
                for line in stats_lines[-10:]:  # Show last 10 lines (summary)
                    print(f"    {line}")

            results["lint"] = False

    if choice in ["2", "3", "6"]:
        print_section("System Tests")
        results["system_check"] = run_command(
            ["python", "check_system.py"], "Running system check", show_output=False
        )

        # Check for test files
        test_files = list(Path("tests").glob("test_*.py")) if Path("tests").exists() else []
        if test_files:
            results["pytest"] = run_command(
                ["pytest", "tests/", "-v", "--tb=short"], "Running pytest", show_output=False
            )
        else:
            print(f"  Running pytest... {YELLOW}⚠ No test files found{NC}")

    if choice in ["4", "6"]:
        print_section("Code Statistics")

        # Count lines of code
        py_files = list(Path(".").glob("*.py"))
        total_lines = 0
        for file in py_files:
            if not any(skip in str(file) for skip in ["backup", "venv", "__pycache__"]):
                with open(file, "r") as f:
                    total_lines += len(f.readlines())

        print(f"  Total Python files: {len(py_files)}")
        print(f"  Total lines of code: {total_lines:,}")

        # Generate detailed lint report
        if choice == "4":
            run_command(
                "flake8 . --max-line-length=100 --ignore=E203,E501,W503 "
                "--exclude=.git,__pycache__,venv,.venv,backup_* --output-file=lint-report.txt",
                "Generating detailed lint report",
            )
            print(f"  {GREEN}Report saved to: lint-report.txt{NC}")

    if choice == "5":
        print_section("Launching DFS Optimizer")
        print(f"{CYAN}Starting GUI...{NC}")
        subprocess.run(["python", "enhanced_dfs_gui.py"])
        return

    # Summary
    print_header("SUMMARY")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    if success_count == total_count:
        print(f"{GREEN}✓ All {total_count} tasks completed successfully!{NC}")
    else:
        print(f"{YELLOW}⚠ {success_count}/{total_count} tasks successful{NC}")
        failed = [k for k, v in results.items() if not v]
        if failed:
            print(f"{RED}Failed: {', '.join(failed)}{NC}")

    # Timing
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"\n{CYAN}Completed in: {duration:.2f} seconds{NC}")

    # Suggestions
    print(f"\n{BOLD}Next steps:{NC}")
    if not results.get("lint", True):
        print("  • Fix lint issues: make fix")
    print("  • Run optimizer: make run")
    print("  • Commit changes: git add -A && git commit -m 'Your message'")


if __name__ == "__main__":
    main()
