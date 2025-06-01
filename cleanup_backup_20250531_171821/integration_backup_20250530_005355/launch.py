#!/usr/bin/env python3
"""
Easy DFS Optimizer Launcher
One-click launch for the high-performance DFS optimizer
"""

import sys
import os
import subprocess

def main():
    print("🚀 DFS Optimizer Launcher")
    print("=" * 30)

    # Check if main launcher exists
    if os.path.exists('main_enhanced_performance.py'):
        print("⚡ Launching High-Performance DFS Optimizer...")
        try:
            subprocess.run([sys.executable, 'main_enhanced_performance.py'] + sys.argv[1:])
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Launch error: {e}")
            print("\nTry running setup again:")
            print("python one_click_setup.py")

    # Fallback launchers
    elif os.path.exists('main_enhanced.py'):
        print("🔧 Launching Enhanced DFS Optimizer...")
        subprocess.run([sys.executable, 'main_enhanced.py'] + sys.argv[1:])

    elif os.path.exists('main.py'):
        print("📁 Launching Basic DFS Optimizer...")
        subprocess.run([sys.executable, 'main.py'] + sys.argv[1:])

    else:
        print("❌ No DFS optimizer found!")
        print("Run setup first: python one_click_setup.py")

if __name__ == "__main__":
    main()
