
#!/usr/bin/env python3
"""
DFS Optimizer - Unified Launcher
The one launcher to rule them all
"""

import sys
import os

def main():
    """Launch the DFS optimizer GUI"""
    print("🚀 DFS Optimizer - Unified Launcher")
    print("=" * 40)

    # Try streamlined GUI first (best option)
    try:
        print("⚡ Launching Streamlined DFS GUI...")
        from streamlined_dfs_gui import main as streamlined_main
        return streamlined_main()
    except ImportError:
        print("   ⚠️ Streamlined GUI not available")
    except Exception as e:
        print(f"   ❌ Streamlined GUI error: {e}")

    # Try enhanced GUI (fallback)
    try:
        print("🔧 Launching Enhanced DFS GUI...")  
        from enhanced_dfs_gui import main as enhanced_main
        return enhanced_main()
    except ImportError:
        print("   ⚠️ Enhanced GUI not available")
    except Exception as e:
        print(f"   ❌ Enhanced GUI error: {e}")

    # Error message
    print("❌ No DFS GUI available!")
    print()
    print("💡 TROUBLESHOOTING:")
    print("   1. Make sure you have PyQt5: pip install PyQt5")
    print("   2. Make sure streamlined_dfs_gui.py exists")
    print("   3. Run: python test_with_sample_data.py")

    return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
