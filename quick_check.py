#!/usr/bin/env python3
"""
SLATE QUICK CHECK
=================
Fast 30-second slate evaluation
"""

import pandas as pd
import sys
from pathlib import Path


def quick_slate_check(csv_file):
    """Quick evaluation of a slate in 30 seconds"""

    print("\n⚡ QUICK SLATE CHECK")
    print("=" * 40)

    df = pd.read_csv(csv_file)

    # Count check marks
    checks = 0
    total_checks = 10

    print("\n✓ = Good  ✗ = Bad  ~ = Neutral\n")

    # 1. Size check
    if len(df) > 250:
        print("✓ Large slate (high variance)")
        checks += 1
    elif len(df) < 150:
        print("✗ Small slate (easy to solve)")
    else:
        print("~ Medium slate")
        checks += 0.5

    # 2. Games check
    num_teams = len(df['TeamAbbrev'].unique())
    num_games = num_teams // 2

    if num_games >= 8:
        print(f"✓ {num_games} games (good variety)")
        checks += 1
    elif num_games <= 4:
        print(f"✗ Only {num_games} games")
    else:
        print(f"~ {num_games} games")
        checks += 0.5

    # 3. Value plays
    values = df[df['Salary'] <= 4000]
    good_values = values[values['AvgPointsPerGame'] >= 20]

    if len(good_values) >= 5:
        print(f"✓ {len(good_values)} strong value plays")
        checks += 1
    elif len(good_values) >= 2:
        print(f"~ {len(good_values)} decent values")
        checks += 0.5
    else:
        print(f"✗ Only {len(good_values)} values")

    # 4. Ace pitchers
    pitchers = df[df['Position'] == 'P']
    aces = pitchers[pitchers['Salary'] >= 9000]

    if 2 <= len(aces) <= 5:
        print(f"✓ {len(aces)} ace pitchers (spread ownership)")
        checks += 1
    elif len(aces) == 1:
        print(f"✗ Single ace (chalk heavy)")
    elif len(aces) > 5:
        print(f"~ {len(aces)} aces (decision paralysis)")
        checks += 0.5
    else:
        print("✗ No clear ace pitchers")

    # 5. Cheap pitchers
    cheap_sp = pitchers[pitchers['Salary'] <= 6000]
    viable_cheap = cheap_sp[cheap_sp['AvgPointsPerGame'] >= 25]

    if len(viable_cheap) >= 3:
        print(f"✓ {len(viable_cheap)} viable SP2 options")
        checks += 1
    elif len(viable_cheap) >= 1:
        print(f"~ {len(viable_cheap)} SP2 option(s)")
        checks += 0.5
    else:
        print("✗ No viable SP2s")

    # 6. Hitting environments
    hitter_parks = ['COL', 'TEX', 'CIN', 'BAL', 'PHI']
    good_hitting = sum(1 for team in df['TeamAbbrev'].unique() if team in hitter_parks)

    if good_hitting >= 4:
        print(f"✓ {good_hitting} hitter-friendly teams")
        checks += 1
    elif good_hitting >= 2:
        print(f"~ {good_hitting} hitter parks")
        checks += 0.5
    else:
        print(f"✗ Limited hitting environments")

    # 7. Salary diversity
    salary_std = df['Salary'].std()
    if salary_std > 2000:
        print("✓ Wide salary range")
        checks += 1
    else:
        print("✗ Narrow salary range")

    # 8. Stack diversity
    teams_with_5plus = sum(1 for team, count in df['TeamAbbrev'].value_counts().items() if count >= 5)

    if teams_with_5plus >= 10:
        print(f"✓ {teams_with_5plus} stackable teams")
        checks += 1
    elif teams_with_5plus >= 6:
        print(f"~ {teams_with_5plus} stackable teams")
        checks += 0.5
    else:
        print(f"✗ Only {teams_with_5plus} stackable teams")

    # 9. Elite plays
    elite = df[df['AvgPointsPerGame'] >= 50]
    if len(elite) >= 10:
        print(f"✓ {len(elite)} elite plays (50+ proj)")
        checks += 1
    elif len(elite) >= 5:
        print(f"~ {len(elite)} elite plays")
        checks += 0.5
    else:
        print(f"✗ Only {len(elite)} elite plays")

    # 10. GPP viability
    df['Value'] = df['AvgPointsPerGame'] / df['Salary'] * 1000
    high_variance = len(df[df['Value'].between(4.5, 6.0)])

    if high_variance >= 20:
        print(f"✓ {high_variance} boom/bust plays")
        checks += 1
    elif high_variance >= 10:
        print(f"~ {high_variance} variance plays")
        checks += 0.5
    else:
        print(f"✗ Low variance slate")

    # Final score
    score = (checks / total_checks) * 100

    print(f"\n{'=' * 40}")
    print(f"SCORE: {score:.0f}/100")

    if score >= 80:
        print("🟢 PLAY THIS SLATE!")
        print("   Excellent opportunities available")
    elif score >= 65:
        print("🟡 PLAYABLE")
        print("   Decent slate, be selective")
    elif score >= 50:
        print("🟠 MARGINAL")
        print("   Only play if you see an edge")
    else:
        print("🔴 SKIP THIS SLATE")
        print("   Wait for better opportunities")

    # Quick recommendations
    print(f"\n💡 QUICK TIPS:")

    if checks >= 7:
        print("• Play 5-10% of bankroll")
        print("• Focus on GPPs")
        print("• Build 20+ unique lineups")
    elif checks >= 5:
        print("• Play 2-5% of bankroll")
        print("• Mix cash and GPPs")
        print("• Focus on your best builds")
    else:
        print("• Max 1% of bankroll")
        print("• Cash games only")
        print("• Wait for better slate")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Find CSV files
        csv_files = list(Path('.').glob('*.csv'))
        if csv_files:
            csv_file = csv_files[0]
            print(f"Using: {csv_file}")
        else:
            print("No CSV files found!")
            sys.exit(1)

    quick_slate_check(csv_file)