#!/usr/bin/env python3
"""
Intelligent Salary Optimization
Automatically analyzes slate size and provides salary recommendations
"""

class SmartSalaryOptimizer:
    """Intelligent salary optimization based on slate characteristics"""

    def __init__(self):
        self.slate_info = {}

    def analyze_slate_and_salary(self, players, lineup_salary=None, budget=50000):
        """Analyze slate and provide salary optimization guidance"""

        total_players = len(players)

        # Estimate games from player distribution
        position_counts = {}
        for player in players:
            pos = getattr(player, 'primary_position', 'UTIL')
            position_counts[pos] = position_counts.get(pos, 0) + 1

        pitcher_count = position_counts.get('P', 0)
        estimated_games = max(1, pitcher_count // 10)  # ~10-12 pitchers per game average

        # Determine slate type and optimal salary targets
        if estimated_games <= 2:
            slate_type = "Tiny"
            min_salary_pct = 98
            target_salary_pct = 99
            strategy = "Must pay up - very limited options"
        elif estimated_games <= 4:
            slate_type = "Small"
            min_salary_pct = 96
            target_salary_pct = 98
            strategy = "Pay up for quality - fewer value plays available"
        elif estimated_games <= 7:
            slate_type = "Medium"
            min_salary_pct = 94
            target_salary_pct = 97
            strategy = "Balanced approach - some value available"
        elif estimated_games <= 12:
            slate_type = "Large"
            min_salary_pct = 92
            target_salary_pct = 96
            strategy = "Can find value - don't overpay"
        else:
            slate_type = "Massive"
            min_salary_pct = 90
            target_salary_pct = 95
            strategy = "Lots of value available - target efficient builds"

        min_salary = int(budget * min_salary_pct / 100)
        target_salary = int(budget * target_salary_pct / 100)

        self.slate_info = {
            'type': slate_type,
            'estimated_games': estimated_games,
            'total_players': total_players,
            'pitcher_count': pitcher_count,
            'min_salary': min_salary,
            'target_salary': target_salary,
            'min_salary_pct': min_salary_pct,
            'target_salary_pct': target_salary_pct,
            'strategy': strategy
        }

        print(f"\n📊 SMART SALARY ANALYSIS:")
        print(f"   Slate Type: {slate_type} ({estimated_games} games estimated)")
        print(f"   Strategy: {strategy}")
        print(f"   Optimal Salary Range: ${min_salary:,} - ${target_salary:,} ({min_salary_pct}%-{target_salary_pct}%)")

        # If lineup salary provided, evaluate it
        if lineup_salary is not None:
            self._evaluate_lineup_salary(lineup_salary, budget)

        return self.slate_info

    def _evaluate_lineup_salary(self, lineup_salary, budget):
        """Evaluate lineup salary usage"""

        usage_pct = (lineup_salary / budget) * 100
        remaining = budget - lineup_salary
        min_target = self.slate_info['min_salary']
        optimal_target = self.slate_info['target_salary']

        print(f"\n💰 LINEUP SALARY EVALUATION:")
        print(f"   Used: ${lineup_salary:,} ({usage_pct:.1f}%)")
        print(f"   Remaining: ${remaining:,}")

        if lineup_salary >= optimal_target:
            print(f"   ✅ EXCELLENT salary usage for {self.slate_info['type']} slate!")
        elif lineup_salary >= min_target:
            shortfall = optimal_target - lineup_salary
            print(f"   ✅ GOOD salary usage")
            print(f"   💡 Could upgrade ${shortfall:,} for better upside")
        else:
            deficit = min_target - lineup_salary
            print(f"   ❌ SUBOPTIMAL for {self.slate_info['type']} slate")
            print(f"   🚨 RECOMMENDATION: Add ${deficit:,} more in salary")

            self._suggest_salary_improvements(deficit)

    def _suggest_salary_improvements(self, deficit):
        """Suggest specific ways to improve salary usage"""

        slate_type = self.slate_info['type']

        print(f"\n🎯 SALARY IMPROVEMENT SUGGESTIONS:")

        if slate_type in ['Tiny', 'Small']:
            print(f"   📈 {slate_type} Slate Strategy: Pay up for premium players")

            if deficit >= 4000:
                print(f"   • Add premium pitcher ($9,000+) + star hitter ($5,000+)")
                print(f"   • Manual picks: 'Gerrit Cole, Aaron Judge'")
            elif deficit >= 2500:
                print(f"   • Add quality starter ($8,000+) + good hitter ($4,500+)")
                print(f"   • Manual picks: 'Shane Bieber, Mookie Betts'")
            elif deficit >= 1500:
                print(f"   • Add one premium player ($6,000+)")
                print(f"   • Manual picks: 'Francisco Lindor' or 'Kyle Tucker'")
            else:
                print(f"   • Upgrade 1-2 positions by $500-800 each")

        elif slate_type == 'Medium':
            print(f"   ⚖️ Medium Slate Strategy: Balanced upgrades")
            if deficit >= 3000:
                print(f"   • Add ace pitcher + premium hitter")
                print(f"   • Manual picks: 'Corbin Burnes, Vladimir Guerrero Jr'")
            else:
                print(f"   • Add one star player")
                print(f"   • Manual picks: 'Shohei Ohtani' or 'Kyle Tucker'")

        else:
            print(f"   📊 Large Slate Strategy: Targeted value upgrades")
            print(f"   • Focus on specific matchup advantages")
            print(f"   • Manual picks: Players with elite matchups")

        print(f"\n🔄 NEXT STEPS:")
        print(f"   1. Add suggested manual picks to your optimizer")
        print(f"   2. Re-run optimization")
        print(f"   3. Target ${self.slate_info['target_salary']:,}+ total salary")

# Global instance for easy access
salary_optimizer = SmartSalaryOptimizer()

def analyze_lineup_salary(players, lineup_salary):
    """Quick function to analyze lineup salary"""
    return salary_optimizer.analyze_slate_and_salary(players, lineup_salary)

def get_slate_recommendations(players):
    """Get slate-specific recommendations"""
    slate_info = salary_optimizer.analyze_slate_and_salary(players)

    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    print(f"   For {slate_info['type']} slates: {slate_info['strategy']}")
    print(f"   Target salary: ${slate_info['min_salary']:,} - ${slate_info['target_salary']:,}")

    if slate_info['type'] in ['Tiny', 'Small']:
        print(f"\n💡 MANUAL PICK SUGGESTIONS:")
        print(f"   Add 2-3 premium confirmed players")
        print(f"   Example: 'Aaron Judge, Gerrit Cole, Mookie Betts'")

    return slate_info

print("✅ Smart salary optimization loaded")
