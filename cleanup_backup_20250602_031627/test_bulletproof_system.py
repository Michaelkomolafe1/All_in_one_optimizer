#!/usr/bin/env python3
"""Basic system test"""

def test_imports():
    try:
        from bulletproof_dfs_core import BulletproofDFSCore
        print("✅ Bulletproof core imports successfully")
        return True
    except Exception as e:
        print(f"❌ Core import failed: {e}")
        return False

if __name__ == "__main__":
    if test_imports():
        print("✅ Basic tests passed")
        exit(0)
    else:
        print("❌ Tests failed") 
        exit(1)
