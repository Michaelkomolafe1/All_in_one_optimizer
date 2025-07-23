#!/usr/bin/env python3
"""
Test the pure data scoring system with real DFS data
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pure_data_scoring_engine import PureDataScoringEngine, PureDataScoringConfig
from unified_core_system import UnifiedMILPOptimizer


def test_real_data_scoring():
    """Test scoring with actual player data"""
    print("\n" + "=" * 60)
    print("TESTING PURE DATA SCORING WITH REAL DATA")
    print("=" * 60)

    # Initialize scoring engine
    config = PureDataScoringConfig()
    engine = PureDataScoringEngine(config)

    # Test data path
    test_file = project_root / "sample_data" / "DFF_Sample_Cheatsheet.csv"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure you have sample data in the sample_data folder")
        return

    # Load sample data
    print(f"\n📁 Loading data from: {test_file}")
    df = pd.read_csv(test_file)

    print(f"✅ Loaded {len(df)} players")
    print(f"📊 Columns: {', '.join(df.columns[:10])}...")  # Show first 10 columns

    # Test scoring on first 5 players
    print("\n" + "-" * 60)
    print("SCORING FIRST 5 PLAYERS:")
    print("-" * 60)

    for idx, row in df.head(5).iterrows():
        player_data = row.to_dict()

        # Calculate score
        score, breakdown = engine.calculate_score(player_data)

        print(f"\n👤 {player_data.get('Name', 'Unknown')} ({player_data.get('Pos', 'N/A')})")
        print(f"   💰 Salary: ${player_data.get('Salary', 0)}")
        print(f"   📊 Base Projection: {player_data.get('base_projection', 0):.2f}")
        print(f"   ⭐ Score: {score:.2f}")
        print(f"   📈 Value: {score / (player_data.get('Salary', 1) / 1000):.2f} pts/$K")

        # Show component breakdown
        if any(v > 0 for v in breakdown.values()):
            print("   Components:")
            for component, value in breakdown.items():
                if value > 0:
                    print(f"      - {component}: {value:.2f}")


def test_optimizer_integration():
    """Test the full optimizer with pure scoring"""
    print("\n\n" + "=" * 60)
    print("TESTING OPTIMIZER INTEGRATION")
    print("=" * 60)

    try:
        # Initialize optimizer
        print("\n🔧 Initializing UnifiedCoreLiteOptimizer...")
        optimizer = UnifiedCoreLiteOptimizer(
            use_pure_scoring=True,  # Use pure data scoring
            debug_mode=True
        )

        # Load test data
        test_file = project_root / "sample_data" / "DFF_Sample_Cheatsheet.csv"
        print(f"📁 Loading slate data...")
        optimizer.load_and_prepare_data(str(test_file))

        print(f"✅ Loaded {len(optimizer.players_df)} players")

        # Show score distribution
        scores = optimizer.players_df['optimization_score'].values
        print(f"\n📊 Score Distribution:")
        print(f"   Min: {scores.min():.2f}")
        print(f"   Max: {scores.max():.2f}")
        print(f"   Mean: {scores.mean():.2f}")
        print(f"   Std: {scores.std():.2f}")

        # Run optimization
        print("\n🚀 Running optimization...")
        lineups = optimizer.optimize(
            num_lineups=3,
            min_salary_usage=0.95,
            diversity_factor=0.10
        )

        if lineups:
            print(f"\n✅ Generated {len(lineups)} lineups!")

            # Show first lineup
            print("\n📋 First Lineup:")
            print("-" * 60)
            first_lineup = lineups[0]

            for player in first_lineup['players']:
                print(f"{player['Name']:20} {player['Pos']:3} ${player['Salary']:5} "
                      f"Proj: {player['base_projection']:5.2f} "
                      f"Score: {player['optimization_score']:5.2f}")

            print(f"\nTotal Salary: ${first_lineup['total_salary']}")
            print(f"Total Projection: {first_lineup['total_projection']:.2f}")
            print(f"Total Score: {first_lineup['total_score']:.2f}")
        else:
            print("❌ No lineups generated")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_data_quality():
    """Check data quality and missing components"""
    print("\n\n" + "=" * 60)
    print("DATA QUALITY ANALYSIS")
    print("=" * 60)

    test_file = project_root / "sample_data" / "DFF_Sample_Cheatsheet.csv"
    df = pd.read_csv(test_file)

    # Check for required fields
    required_fields = ['base_projection', 'Name', 'Pos', 'Salary']
    optional_fields = ['vegas_total', 'recent_avg', 'batting_order', 'matchup_score']

    print("\n📋 Required Fields:")
    for field in required_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            print(f"   ✅ {field}: {non_null}/{len(df)} ({non_null / len(df) * 100:.1f}%)")
        else:
            print(f"   ❌ {field}: MISSING")

    print("\n📋 Optional Fields (for scoring components):")
    for field in optional_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            print(f"   {'✅' if non_null > 0 else '⚠️'} {field}: {non_null}/{len(df)} ({non_null / len(df) * 100:.1f}%)")
        else:
            print(f"   ❌ {field}: MISSING")

    # Show players with complete data
    complete_mask = df['base_projection'].notna()
    for field in optional_fields:
        if field in df.columns:
            complete_mask &= df[field].notna()

    complete_count = complete_mask.sum()
    print(f"\n📊 Players with complete data: {complete_count}/{len(df)} ({complete_count / len(df) * 100:.1f}%)")

    if complete_count > 0:
        print("\n👥 Sample of complete players:")
        complete_players = df[complete_mask].head(3)
        for _, player in complete_players.iterrows():
            print(f"   - {player['Name']} ({player['Pos']}): {player['base_projection']:.2f} pts")


if __name__ == "__main__":
    # Run all tests
    test_real_data_scoring()
    test_optimizer_integration()
    test_data_quality()

    print("\n\n✅ All tests completed!")
    print("\n💡 Next steps:")
    print("1. Review the score distribution - are scores reasonable?")
    print("2. Check if lineups make sense (studs + value plays)")
    print("3. Verify data quality - which components are missing?")
    print("4. Run GUI to see visual results")