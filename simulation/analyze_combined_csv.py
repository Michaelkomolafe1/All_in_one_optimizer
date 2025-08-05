#!/usr/bin/env python3
"""
COMBINE ML TRAINING DATA
========================
Combines all difficulty levels into one comprehensive dataset
"""

import pandas as pd
import os
import glob
from datetime import datetime


def combine_ml_datasets():
    """Combine all ML training CSV files"""

    print("🔄 COMBINING ML TRAINING DATA")
    print("=" * 50)

    # Find all ML training files
    csv_files = {
        'easy': 'ml_training_data_easy_20250805_024952.csv',
        'medium': 'ml_training_data_medium_20250805_024828.csv',
        'hard': 'ml_training_data_hard_20250805_024220.csv',
        'extreme': 'ml_training_data_extreme_20250805_024501.csv'
    }

    all_dfs = []
    total_records = 0

    # Load each file
    for difficulty, filename in csv_files.items():
        if os.path.exists(filename):
            print(f"\n📂 Loading {difficulty} data...")
            df = pd.read_csv(filename)

            # Add difficulty column if not present
            if 'difficulty_level' not in df.columns:
                df['difficulty_level'] = difficulty

            print(f"   Records: {len(df):,}")
            print(f"   Columns: {len(df.columns)}")
            print(f"   Win rate: {df['lineup_win'].mean() * 100:.1f}%")

            all_dfs.append(df)
            total_records += len(df)
        else:
            print(f"⚠️  File not found: {filename}")

    if not all_dfs:
        print("❌ No data files found!")
        return None

    # Combine all dataframes
    print(f"\n🔗 Combining {len(all_dfs)} datasets...")
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Save combined dataset
    output_file = f'ml_training_data_combined_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    combined_df.to_csv(output_file, index=False)

    print(f"\n✅ Combined dataset saved: {output_file}")
    print(f"   Total records: {len(combined_df):,}")
    print(f"   Unique slates: {combined_df['slate_id'].nunique():,}")
    print(f"   Difficulty distribution:")
    print(combined_df['difficulty_level'].value_counts())

    # Show overall statistics
    print("\n📊 OVERALL STATISTICS:")
    print(f"   Average win rate: {combined_df['lineup_win'].mean() * 100:.1f}%")
    print(f"   Average ROI: {combined_df['lineup_roi'].mean():.1f}%")

    # Show by difficulty
    print("\n📈 Performance by Difficulty:")
    for difficulty in ['easy', 'medium', 'hard', 'extreme']:
        diff_data = combined_df[combined_df['difficulty_level'] == difficulty]
        if len(diff_data) > 0:
            win_rate = diff_data['lineup_win'].mean() * 100
            avg_roi = diff_data['lineup_roi'].mean()
            print(f"   {difficulty:8s}: {win_rate:5.1f}% win rate, {avg_roi:+6.1f}% ROI")

    # Show by strategy
    print("\n🎯 Performance by Strategy:")
    for strategy in combined_df['strategy'].unique():
        strat_data = combined_df[combined_df['strategy'] == strategy]
        win_rate = strat_data['lineup_win'].mean() * 100
        count = len(strat_data) // 10  # Divide by 10 to get lineup count
        print(f"   {strategy:25s}: {win_rate:5.1f}% win rate ({count} lineups)")

    # Feature analysis
    print("\n🔍 Feature Availability:")
    important_features = [
        'salary', 'projection', 'optimization_score',
        'lineup_score', 'lineup_rank', 'lineup_win',
        'position', 'strategy', 'contest_type'
    ]

    for feature in important_features:
        if feature in combined_df.columns:
            null_pct = combined_df[feature].isnull().mean() * 100
            print(f"   {feature:20s}: ✓ ({100 - null_pct:.1f}% complete)")
        else:
            print(f"   {feature:20s}: ✗ (missing)")

    return output_file


if __name__ == "__main__":
    # Run combination
    output_file = combine_ml_datasets()

    if output_file:
        print(f"\n🚀 NEXT STEPS:")
        print("1. Run the simplified ML workflow:")
        print("   python simulation/simplified_ml_workflow.py")
        print("2. When prompted, use this combined file:")
        print(f"   {output_file}")
        print("3. Choose 'medium' difficulty for balanced training")
        print("4. Select 'N' for full training (not quick mode)")