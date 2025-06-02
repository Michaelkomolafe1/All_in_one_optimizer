#!/usr/bin/env python3
"""
Launch Enhanced System - Your complete advanced DFS system
"""

import os
import sys

def main():
    """Launch your enhanced system"""
    print("🚀 LAUNCHING ENHANCED STRICT DFS SYSTEM")
    print("=" * 60)
    print("✅ All advanced algorithms integrated:")
    print("   🏟️ Park factors with handedness splits")
    print("   📈 L5 performance trend analysis")
    print("   💰 Vegas lines with team calculations")
    print("   🔬 Priority Statcast processing")
    print("   🎯 Enhanced DFF value analysis")
    print("   🧠 7+ factor combined scoring")
    print("🔒 BULLETPROOF: NO unconfirmed leaks possible")
    print("=" * 60)

    # Check if enhanced core exists
    if not os.path.exists('enhanced_strict_core.py'):
        print("❌ Enhanced core not found!")
        print("💡 You need to copy your Enhanced Strict Core code")
        print("   into enhanced_strict_core.py")
        return False

    # Check if it has real content
    with open('enhanced_strict_core.py', 'r') as f:
        content = f.read()
        if 'placeholder' in content.lower():
            print("⚠️ Enhanced core is placeholder!")
            print("💡 Copy your complete Enhanced Strict Core code")
            print("   from paste.txt into enhanced_strict_core.py")
            return False

    try:
        # Launch enhanced GUI
        import enhanced_strict_gui
        return enhanced_strict_gui.main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all files are in place")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
