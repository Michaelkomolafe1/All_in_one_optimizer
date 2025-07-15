#!/usr/bin/env python3
"""
SIMPLE ALL-STAR OPTIMIZER - NO DEPENDENCIES
===========================================

This works with just Python standard library + your existing core system.
No PyQt needed - just optimization!
"""

import sys
import os
import csv
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, '.')


def find_csv_files():
    """Find CSV files in Downloads and current directory"""
    csv_files = []

    # Check Downloads folder
    downloads_path = os.path.expanduser("~/Downloads")
    if os.path.exists(downloads_path):
        for file in os.listdir(downloads_path):
            if file.endswith('.csv') and ('salary' in file.lower() or 'dk' in file.lower()):
                csv_files.append(os.path.join(downloads_path, file))

    # Check current directory
    for file in os.listdir('.'):
        if file.endswith('.csv') and ('salary' in file.lower() or 'dk' in file.lower()):
            csv_files.append(file)

    # Sort by modification time (newest first)
    csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return csv_files


def load_csv_simple(csv_path):
    """Load CSV with simple parsing"""
    print(f"📄 Loading CSV: {os.path.basename(csv_path)}")

    players = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    # Handle different CSV column names
                    name = row.get('Name', row.get('name', '')).strip()
                    team = row.get('TeamAbbrev', row.get('Team', row.get('team', ''))).strip()
                    salary = int(row.get('Salary', row.get('salary', 0)))
                    projection = float(row.get('AvgPointsPerGame', row.get('projection', row.get('Projection', 0))))
                    position = row.get('Position', row.get('position', 'UTIL')).strip()

                    if name and salary > 0:
                        player = {
                            'name': name,
                            'team': team,
                            'salary': salary,
                            'projection': projection,
                            'position': position,
                            'value': projection / max(salary, 1000) * 1000,
                            'is_captain': False,
                            'is_allstar': False
                        }
                        players.append(player)

                except Exception as e:
                    print(f"⚠️ Error parsing row {i}: {e}")
                    continue

        print(f"✅ Loaded {len(players)} players")
        return players

    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []


def mark_allstar_players(players):
    """Mark confirmed All-Star players from the lineups you provided"""
    # All-Star lineups from your message
    allstar_names = [
        "Gleyber Torres", "Riley Greene", "Aaron Judge", "Cal Raleigh",
        "Vladimir Guerrero Jr.", "Ryan O'Hearn", "Junior Caminero",
        "Javier Báez", "Jacob Wilson", "Tarik Skubal",
        "Shohei Ohtani", "Ronald Acuña Jr.", "Ketel Marte", "Freddie Freeman",
        "Manny Machado", "Will Smith", "Kyle Tucker", "Francisco Lindor",
        "Pete Crow-Armstrong", "Paul Skenes"
    ]

    print(f"\n⭐ MARKING ALL-STAR PLAYERS...")
    marked_count = 0

    for player in players:
        for allstar in allstar_names:
            # Flexible name matching
            if (allstar.lower() in player['name'].lower() or
                    player['name'].lower() in allstar.lower() or
                    any(part in player['name'].lower() for part in allstar.lower().split())):
                player['is_allstar'] = True
                marked_count += 1
                print(f"   ⭐ {player['name']} ({player['team']}) - ${player['salary']:,}")
                break

    print(f"\n✅ Marked {marked_count} confirmed All-Star players")
    return marked_count


def optimize_showdown_simple(players):
    """Simple showdown optimization using greedy algorithm"""
    print(f"\n🎰 SIMPLE SHOWDOWN OPTIMIZATION")
    print("=" * 60)

    if len(players) < 6:
        print(f"❌ Need at least 6 players, only have {len(players)}")
        return None

    # Separate All-Stars and others, sort by value
    allstars = [p for p in players if p['is_allstar']]
    others = [p for p in players if not p['is_allstar']]

    # Sort each group by value (points per $1000)
    allstars.sort(key=lambda p: p['value'], reverse=True)
    others.sort(key=lambda p: p['value'], reverse=True)

    # Combine with All-Stars first (prioritize confirmed players)
    ordered_players = allstars + others

    print(f"📊 Optimization pool: {len(allstars)} All-Stars + {len(others)} others")
    print(f"   Top values: {ordered_players[0]['name']} ({ordered_players[0]['value']:.1f})")

    # Greedy selection algorithm
    lineup = []
    total_salary = 0

    # Step 1: Select Captain (highest value that fits budget)
    print(f"\n👑 SELECTING CAPTAIN...")
    captain_selected = False

    for player in ordered_players:
        captain_cost = int(player['salary'] * 1.5)
        if captain_cost <= 35000:  # Leave room for 5 utilities
            player['is_captain'] = True
            lineup.append(player)
            total_salary += captain_cost
            captain_selected = True

            star_indicator = "⭐" if player['is_allstar'] else ""
            print(f"   Selected: {player['name']} {star_indicator}")
            print(f"   Team: {player['team']} | Position: {player['position']}")
            print(f"   Captain cost: ${captain_cost:,} | Value: {player['value']:.1f}")
            break

    if not captain_selected:
        print(f"❌ Could not select captain within budget")
        return None

    # Step 2: Select 5 Utility Players
    print(f"\n⚡ SELECTING UTILITY PLAYERS...")
    remaining_players = [p for p in ordered_players if p not in lineup]
    remaining_budget = 50000 - total_salary
    utilities_selected = 0

    print(f"   Remaining budget: ${remaining_budget:,}")

    for player in remaining_players:
        if utilities_selected >= 5:
            break

        if player['salary'] <= remaining_budget:
            player['is_captain'] = False
            lineup.append(player)
            total_salary += player['salary']
            remaining_budget -= player['salary']
            utilities_selected += 1

            star_indicator = "⭐" if player['is_allstar'] else ""
            print(f"   {utilities_selected}. {player['name']} {star_indicator}")
            print(f"      Team: {player['team']} | Salary: ${player['salary']:,} | Value: {player['value']:.1f}")

    if len(lineup) == 6:
        print(f"\n✅ LINEUP COMPLETE!")
        print(f"   Total players: {len(lineup)}")
        print(f"   Total salary: ${total_salary:,} / $50,000")
        print(f"   Remaining: ${50000 - total_salary:,}")
        return lineup
    else:
        print(f"\n❌ Could only select {len(lineup)}/6 players")
        print(f"   Budget remaining: ${remaining_budget:,}")
        return lineup if lineup else None


def display_final_lineup(lineup):
    """Display the final optimized lineup"""
    if not lineup:
        print("❌ No lineup to display")
        return

    print(f"\n🏆 FINAL ALL-STAR SHOWDOWN LINEUP")
    print("=" * 70)

    captain = next((p for p in lineup if p['is_captain']), None)
    utilities = [p for p in lineup if not p['is_captain']]

    total_salary = 0
    total_points = 0
    allstar_count = 0

    # Display Captain
    if captain:
        cap_salary = int(captain['salary'] * 1.5)
        cap_points = captain['projection'] * 1.5
        total_salary += cap_salary
        total_points += cap_points

        if captain['is_allstar']:
            allstar_count += 1

        star_indicator = "⭐ ALL-STAR" if captain['is_allstar'] else ""
        print(f"👑 CAPTAIN: {captain['name']} {star_indicator}")
        print(f"   Team: {captain['team']} | Position: {captain['position']}")
        print(f"   Base Salary: ${captain['salary']:,} → Captain: ${cap_salary:,}")
        print(f"   Base Points: {captain['projection']:.1f} → Captain: {cap_points:.1f}")
        print(f"   Value Score: {captain['value']:.1f}")

    # Display Utility Players
    print(f"\n⚡ UTILITY PLAYERS:")
    for i, player in enumerate(utilities, 1):
        total_salary += player['salary']
        total_points += player['projection']

        if player['is_allstar']:
            allstar_count += 1

        star_indicator = "⭐" if player['is_allstar'] else ""
        print(f"{i}. {player['name']} {star_indicator}")
        print(f"   Team: {player['team']} | Position: {player['position']}")
        print(f"   Salary: ${player['salary']:,} | Points: {player['projection']:.1f}")
        print(f"   Value Score: {player['value']:.1f}")

    # Summary Statistics
    print(f"\n📊 LINEUP SUMMARY:")
    print(f"💰 Total Salary: ${total_salary:,} / $50,000")
    print(f"💰 Remaining Budget: ${50000 - total_salary:,}")
    print(f"📈 Projected Points: {total_points:.1f}")
    print(f"⭐ All-Stars in Lineup: {allstar_count}/6")
    print(f"🎯 Average Value Score: {sum(p['value'] for p in lineup) / len(lineup):.1f}")

    # Team Distribution
    teams = {}
    for player in lineup:
        teams[player['team']] = teams.get(player['team'], 0) + 1

    print(f"🏈 Team Distribution:")
    for team, count in sorted(teams.items()):
        print(f"   {team}: {count} player{'s' if count > 1 else ''}")

    # Export option
    print(f"\n💾 LINEUP EXPORT:")
    export_text = []

    if captain:
        export_text.append(
            f"CPT,{captain['name']},{captain['team']},{captain['position']},{int(captain['salary'] * 1.5)},{captain['projection'] * 1.5:.1f}")

    for i, player in enumerate(utilities, 1):
        export_text.append(
            f"UTIL{i},{player['name']},{player['team']},{player['position']},{player['salary']},{player['projection']:.1f}")

    print("   Copy this for DraftKings:")
    for line in export_text:
        print(f"   {line}")


def main():
    """Main execution function"""
    print("🌟 SIMPLE ALL-STAR SHOWDOWN OPTIMIZER")
    print("=" * 70)
    print("🎯 Optimizing for DraftKings Showdown format")
    print("   1 Captain (1.5x points & salary) + 5 Utilities")
    print("   $50,000 salary cap")

    # Find CSV files
    csv_files = find_csv_files()

    if not csv_files:
        print("❌ No CSV files found!")
        print("   Looking for files with 'salary' or 'dk' in name")
        print("   Checked: ~/Downloads and current directory")
        csv_path = input("\nEnter full path to CSV file: ").strip()
    else:
        print(f"\n📁 Found {len(csv_files)} CSV file(s):")
        for i, file in enumerate(csv_files, 1):
            print(f"   {i}. {os.path.basename(file)} ({os.path.getmtime(file)})")

        if len(csv_files) == 1:
            csv_path = csv_files[0]
            print(f"\n✅ Using: {os.path.basename(csv_path)}")
        else:
            # Auto-select the newest one (likely DKSalaries(6).csv)
            csv_path = csv_files[0]
            print(f"\n✅ Auto-selected newest: {os.path.basename(csv_path)}")

    # Load players
    players = load_csv_simple(csv_path)
    if not players:
        print("❌ Failed to load players from CSV")
        return

    # Show basic stats
    print(f"\n📊 PLAYER STATISTICS:")
    print(f"   Total players: {len(players)}")
    print(f"   Salary range: ${min(p['salary'] for p in players):,} - ${max(p['salary'] for p in players):,}")
    print(
        f"   Projection range: {min(p['projection'] for p in players):.1f} - {max(p['projection'] for p in players):.1f}")

    # Mark All-Star players
    allstar_count = mark_allstar_players(players)

    # Optimize lineup
    lineup = optimize_showdown_simple(players)

    # Display results
    if lineup:
        display_final_lineup(lineup)
        print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
        print(f"🎯 Ready to copy into DraftKings!")
    else:
        print(f"\n❌ OPTIMIZATION FAILED")
        print(f"💡 Try adjusting salary constraints or player pool")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Optimization cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()