#!/usr/bin/env python3
"""
DFS Optimizer CLI - Command line interface for the unified system
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="DFS Optimizer CLI")
    parser.add_argument('--dk', required=True, help='DraftKings CSV file')
    parser.add_argument('--dff', help='DFF rankings CSV file')
    parser.add_argument('--manual', default='', help='Manual player selections (comma separated)')
    parser.add_argument('--contest', choices=['classic', 'showdown'], default='classic', help='Contest type')
    parser.add_argument('--strategy', 
                       choices=['smart_confirmed', 'confirmed_only', 'confirmed_plus_manual', 
                               'confirmed_pitchers_all_batters', 'manual_only', 'all_players'],
                       default='smart_confirmed', help='Strategy filter')
    parser.add_argument('--budget', type=int, default=50000, help='Salary budget')
    parser.add_argument('--output', help='Output file for lineup')

    args = parser.parse_args()

    # Check if DK file exists
    if not Path(args.dk).exists():
        print(f"❌ DraftKings file not found: {args.dk}")
        return 1

    # Check if DFF file exists (if specified)
    if args.dff and not Path(args.dff).exists():
        print(f"❌ DFF file not found: {args.dff}")
        return 1

    print("🚀 DFS OPTIMIZER CLI")
    print(f"📁 DK File: {args.dk}")
    print(f"🎯 Strategy: {args.strategy}")
    print(f"💰 Budget: ${args.budget:,}")

    try:
        # Use unified pipeline
        from cleanup_backup_20250531_105034.working_dfs_core_final import load_and_optimize_complete_pipeline_enhanced

        lineup, score, summary = load_and_optimize_complete_pipeline_enhanced(
            dk_file=args.dk,
            dff_file=args.dff,
            manual_input=args.manual,
            contest_type=args.contest,
            strategy=args.strategy
        )

        if lineup and score > 0:
            print(f"\n✅ SUCCESS: Generated lineup with {score:.2f} points")
            print("\n" + summary)

            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(summary)
                print(f"\n💾 Saved to: {args.output}")

            return 0
        else:
            print("\n❌ Failed to generate lineup")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
