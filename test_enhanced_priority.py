#!/usr/bin/env python3
"""
Simple Test Launcher - Tests with enhanced priority detection
"""

def main():
    print("🚀 TESTING ENHANCED PRIORITY DETECTION")
    print("=" * 60)

    try:
        # First run the enhancement
        print("🔧 Applying enhanced priority detection...")
        import enhance_priority_detection

        # Then test with manual players
        print("\n🧪 Testing with manual priority players...")
        import test_manual_priority

        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
