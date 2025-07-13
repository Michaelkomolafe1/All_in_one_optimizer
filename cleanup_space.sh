#!/bin/bash
echo "🧹 Cleaning up space..."

# Remove Python caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Remove logs
find . -name "*.log" -delete 2>/dev/null

# Clean data caches
rm -rf data/cache/* 2>/dev/null
rm -rf .pytest_cache 2>/dev/null

# Show new size
echo "✅ Cleanup complete!"
du -sh .
