#!/usr/bin/env python3
"""
Lineup Validator Integration Helper
==================================
Helper functions for integrating lineup validator with bulletproof core
"""

def add_validation_methods_to_core():
    """Returns the methods to add to BulletproofDFSCore class"""

    methods_code = """
    def validate_current_lineup(self):
        """Validate current manually selected players"""
        try:
            from smart_lineup_validator import SmartLineupValidator

            # Get currently selected players
            selected_players = [p for p in self.players if getattr(p, 'is_manual_selected', False)]

            # Create validator and run validation
            validator = SmartLineupValidator(self.salary_cap)
            validation_result = validator.validate_lineup(selected_players)

            return validation_result

        except ImportError:
            return {'error': 'Smart lineup validator not available'}
        except Exception as e:
            return {'error': f'Validation failed: {str(e)}'}

    def print_lineup_status(self):
        """Print current lineup status to console"""
        try:
            from smart_lineup_validator import SmartLineupValidator

            selected_players = [p for p in self.players if getattr(p, 'is_manual_selected', False)]

            if not selected_players:
                print("\n📋 No players manually selected yet")
                print("💡 Add players with: enhanced manual selection")
                return

            validator = SmartLineupValidator(self.salary_cap)
            summary = validator.get_lineup_summary(selected_players)
            print(f"\n{summary}")

        except ImportError:
            print("⚠️ Smart lineup validator not available")
        except Exception as e:
            print(f"❌ Status check failed: {e}")

    def get_smart_recommendations(self, max_recommendations=5):
        """Get smart player recommendations based on current lineup"""
        try:
            from smart_lineup_validator import get_value_recommendations

            selected_players = [p for p in self.players if getattr(p, 'is_manual_selected', False)]

            recommendations = get_value_recommendations(
                selected_players, self.players, max_recommendations
            )

            if recommendations:
                print(f"\n🎯 TOP {len(recommendations)} RECOMMENDATIONS:")
                print("-" * 40)

                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec['player_name']} ({rec['position']})")
                    print(f"   💰 ${rec['salary']:,} | 📊 {rec['projected_score']:.1f} pts")
                    print(f"   📈 Value: {rec['value_score']:.2f} pts/$1K")
                    print()
            else:
                print("\n💡 No recommendations available")

            return recommendations

        except ImportError:
            print("⚠️ Smart recommendations not available")
            return []
        except Exception as e:
            print(f"❌ Recommendations failed: {e}")
            return []
"""

    return methods_code
