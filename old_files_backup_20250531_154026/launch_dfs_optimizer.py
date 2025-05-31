#!/usr/bin/env python3
"""
DFS Optimizer Launcher - Automatically uses best available system
"""

import sys
import os

def main():
    """Launch the best available DFS GUI"""
    print("🚀 DFS OPTIMIZER LAUNCHER")
    print("=" * 30)

    # Try streamlined GUI first
    try:
        print("⚡ Launching Streamlined DFS GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI 
    try:
        print("🔧 Launching Enhanced DFS GUI...")
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    print("❌ No GUI available!")
    print("💡 Make sure PyQt5 is installed: pip install PyQt5")
    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
