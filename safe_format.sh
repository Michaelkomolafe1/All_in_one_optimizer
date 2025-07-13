#!/bin/bash
# Safe formatting script that won't break your code

echo "🧹 Safe Code Formatting"
echo "======================"

# 1. Create a safety backup first
echo "📦 Creating safety backup..."
mkdir -p .format_backup
cp *.py .format_backup/

# 2. Run autoflake (safely)
echo "🔧 Removing unused imports..."
autoflake --remove-all-unused-imports --remove-unused-variables --in-place *.py

# 3. Run isort
echo "📑 Sorting imports..."
isort *.py

# 4. Run black
echo "🎨 Formatting with Black..."
black *.py

# 5. Check if everything still works
echo "✅ Checking system health..."
python check_system.py

echo "✨ Done!"
