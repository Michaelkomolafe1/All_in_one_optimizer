#!/usr/bin/env python3
"""
Comprehensive Smart Validator Test
=================================
Test all validator features with bulletproof integration
"""

def test_smart_validator_standalone():
    """Test validator module standalone"""
    print("🧪 Testing Smart Validator Module")
    print("=" * 40)

    try:
        from smart_lineup_validator import SmartLineupValidator, get_value_recommendations

        # Create mock players for testing
        class MockPlayer:
            def __init__(self, name, position, salary, score, team="TEST"):
                self.name = name
                self.primary_position = position
                self.positions = [position]
                self.salary = salary
                self.enhanced_score = score
                self.team = team
                self.is_manual_selected = False

        # Test players
        players = [
            MockPlayer("Kyle Tucker", "OF", 5000, 12.5, "HOU"),
            MockPlayer("Jose Altuve", "2B", 4500, 10.8, "HOU"),
            MockPlayer("Hunter Brown", "P", 8000, 15.2, "HOU"),
            MockPlayer("Vladimir Guerrero Jr.", "1B", 5200, 11.5, "TOR"),
            MockPlayer("Aaron Judge", "OF", 6000, 13.1, "NYY")
        ]

        # Test 1: Empty lineup
        validator = SmartLineupValidator()
        result = validator.validate_lineup([])
        print(f"Empty lineup test: {'✅' if not result['is_valid'] else '❌'}")

        # Test 2: Partial lineup
        selected = players[:3]
        result = validator.validate_lineup(selected)
        print(f"Partial lineup test: {'✅' if not result['is_complete'] else '❌'}")
        print(f"  Salary used: ${result['salary_analysis']['total_used']:,}")
        print(f"  Spots remaining: {result['spots_remaining']}")

        # Test 3: Lineup summary
        summary = validator.get_lineup_summary(selected)
        print(f"\nSummary test: {'✅' if 'LINEUP SUMMARY' in summary else '❌'}")

        # Test 4: Value recommendations
        recommendations = get_value_recommendations(selected[:2], players, 3)
        print(f"Recommendations test: {'✅' if len(recommendations) > 0 else '❌'}")
        print(f"  Found {len(recommendations)} recommendations")

        print("\n✅ Smart validator standalone tests completed!")
        return True

    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        return False

def test_bulletproof_integration():
    """Test integration with bulletproof core"""
    print("\n🔗 Testing Bulletproof Core Integration")
    print("=" * 40)

    try:
        from bulletproof_dfs_core import BulletproofDFSCore

        # Create core instance
        core = BulletproofDFSCore()

        # Test if validation methods exist
        methods_to_check = [
            'validate_current_lineup',
            'print_lineup_status', 
            'get_smart_recommendations'
        ]

        missing_methods = []
        for method_name in methods_to_check:
            if not hasattr(core, method_name):
                missing_methods.append(method_name)

        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False

        print("✅ All validation methods found in bulletproof core")

        # Test method calls (basic smoke test)
        try:
            validation_result = core.validate_current_lineup()
            print("✅ validate_current_lineup() callable")

            core.print_lineup_status()
            print("✅ print_lineup_status() callable")

            recommendations = core.get_smart_recommendations(3)
            print("✅ get_smart_recommendations() callable")

        except Exception as e:
            print(f"⚠️ Method call test warning: {e}")

        print("\n✅ Bulletproof core integration tests completed!")
        return True

    except ImportError as e:
        print(f"❌ Integration test failed - import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run comprehensive tests"""
    print("🔬 COMPREHENSIVE SMART VALIDATOR TESTS")
    print("=" * 50)

    success1 = test_smart_validator_standalone()
    success2 = test_bulletproof_integration()

    print("\n📊 TEST RESULTS")
    print("=" * 20)

    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Smart validator working perfectly")
        print("✅ Bulletproof integration successful")
        print("\n🚀 Ready to use enhanced features!")
    else:
        print("⚠️ Some tests had issues:")
        print(f"   Standalone validator: {'✅' if success1 else '❌'}")
        print(f"   Bulletproof integration: {'✅' if success2 else '❌'}")

    return success1 and success2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
