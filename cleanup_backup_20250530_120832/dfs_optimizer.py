#!/usr/bin/env python3
"""
DFS Optimizer - Unified Launcher
Created by Integration Wizard
"""

import sys
import os

def main():
    """Launch the best available DFS optimizer GUI"""
    print("🚀 DFS Optimizer - Unified Launcher")
    print("=" * 40)

    # Try streamlined GUI first (best option)
    try:
        print("⚡ Launching Streamlined DFS Optimizer...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI (fallback)
    try:
        print("🔧 Launching Enhanced DFS Optimizer...")  
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    # Error message
    print("❌ No DFS Optimizer GUI available!")
    print()
    print("💡 TROUBLESHOOTING:")
    print("   1. Make sure you have PyQt5: pip install PyQt5")
    print("   2. Check you have the GUI files:")
    print("      - streamlined_dfs_gui.py (recommended)")
    print("      - enhanced_dfs_gui.py (fallback)")
    print("   3. Run integration wizard again if needed")

    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
