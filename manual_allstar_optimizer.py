#!/usr/bin/env python3
"""
MANUAL ALL-STAR SHOWDOWN OPTIMIZER
==================================
Simple script to manually optimize All-Star showdown lineups
"""

import csv
import os
from typing import List, Dict

class SimplePlayer:
    def __init__(self, name, team, salary, projection, position):
        self.name = name
        self.team = team
        self.salary = int(salary)
        self.projection = float(projection)
        self.position = position
        self.value = self.projection / max(self.salary, 1000) * 1000
        self.is_captain = False
        self.is_allstar = False

def load_csv_simple(csv_path):
    """Load CSV with simple parsing"""
    players = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                player = SimplePlayer(
                    name=row.get('Name', '').strip(),
                    team=row.get('TeamAbbrev', '').strip(),
                    salary=row.get('Salary', 0),
                    projection=row.get('AvgPointsPerGame', 0),
                    position=row.get('Position', 'UTIL')
                )
                players.append(player)
            except:
                continue

    return players

def mark_allstar_players(players):
    """Mark confirmed All-Star players"""
    # All-Star lineups from your message
    allstar_names = [
        "Gleyber Torres", "Riley Greene", "Aaron Judge", "Cal Raleigh",
        "Vladimir Guerrero Jr.", "Ryan O'Hearn", "Junior Caminero", 
        "Javier Báez", "Jacob Wilson", "Tarik Skubal",
        "Shohei Ohtani", "Ronald Acuña Jr.", "Ketel Marte", "Freddie Freeman",
        "Manny Machado", "Will Smith", "Kyle Tucker", "Francisco Lindor",
        "Pete Crow-Armstrong", "Paul Skenes"
    ]

    marked_count = 0
    for player in players:
        for allstar in allstar_names:
            if allstar.lower() in player.name.lower() or player.name.lower() in allstar.lower():
                player.is_allstar = True
                marked_count += 1
                print(f"⭐ All-Star: {player.name}")
                break

    print(f"\n✅ Marked {marked_count} All-Star players")
    return marked_count

def simple_showdown_optimize(players):
    """Simple showdown optimization"""
    print(f"\n🎯 SIMPLE SHOWDOWN OPTIMIZATION")
    print("=" * 50)

    # Prefer All-Stars, then by value
    allstars = [p for p in players if p.is_allstar]
    others = [p for p in players if not p.is_allstar]

    # Sort each group by value
    allstars.sort(key=lambda p: p.value, reverse=True)
    others.sort(key=lambda p: p.value, reverse=True)

    # Combine with All-Stars first
    ordered_players = allstars + others

    print(f"📊 {len(allstars)} All-Stars + {len(others)} others")

    # Greedy selection
    lineup = []
    total_salary = 0

    # Select captain
    for player in ordered_players:
        captain_cost = int(player.salary * 1.5)
        if captain_cost <= 30000:  # Leave room for utilities
            player.is_captain = True
            lineup.append(player)
            total_salary += captain_cost
            print(f"👑 Captain: {player.name} (${captain_cost:,})")
            break

    if not lineup:
        print("❌ Could not select captain")
        return None

    # Select 5 utilities
    remaining = [p for p in ordered_players if p not in lineup]
    remaining_budget = 50000 - total_salary

    for player in remaining:
        if len(lineup) >= 6:
            break
        if player.salary <= remaining_budget:
            lineup.append(player)
            total_salary += player.salary
            remaining_budget -= player.salary
            print(f"⚡ Util: {player.name} (${player.salary:,})")

    if len(lineup) == 6:
        print(f"\n✅ Lineup complete: ${total_salary:,} / $50,000")
        return lineup
    else:
        print(f"❌ Only selected {len(lineup)}/6 players")
        return None

def display_final_lineup(lineup):
    """Display final lineup"""
    if not lineup:
        print("❌ No lineup to display")
        return

    print(f"\n🏆 FINAL ALL-STAR SHOWDOWN LINEUP")
    print("=" * 60)

    captain = next((p for p in lineup if p.is_captain), None)
    utilities = [p for p in lineup if not p.is_captain]

    total_salary = 0
    total_points = 0

    if captain:
        cap_salary = int(captain.salary * 1.5)
        cap_points = captain.projection * 1.5
        total_salary += cap_salary
        total_points += cap_points

        star_indicator = "⭐" if captain.is_allstar else ""
        print(f"👑 CAPTAIN: {captain.name} {star_indicator}")
        print(f"   Team: {captain.team} | Pos: {captain.position}")
        print(f"   Salary: ${cap_salary:,} | Points: {cap_points:.1f}")

    print(f"\n⚡ UTILITY PLAYERS:")
    for i, player in enumerate(utilities, 1):
        total_salary += player.salary
        total_points += player.projection

        star_indicator = "⭐" if player.is_allstar else ""
        print(f"{i}. {player.name} {star_indicator}")
        print(f"   Team: {player.team} | Pos: {player.position}")
        print(f"   Salary: ${player.salary:,} | Points: {player.projection:.1f}")

    print(f"\n📊 TOTALS:")
    print(f"💰 Salary: ${total_salary:,} / $50,000 (${50000-total_salary:,} remaining)")
    print(f"📈 Projected Points: {total_points:.1f}")

    allstar_count = sum(1 for p in lineup if p.is_allstar)
    print(f"⭐ All-Stars in lineup: {allstar_count}/6")

def main():
    """Main execution"""
    print("🌟 MANUAL ALL-STAR SHOWDOWN OPTIMIZER")
    print("=" * 60)

    # Find CSV file
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'salary' in f.lower()]

    if not csv_files:
        csv_path = input("Enter CSV file path: ")
    else:
        csv_path = csv_files[-1]
        print(f"📄 Using: {csv_path}")

    # Load players
    players = load_csv_simple(csv_path)
    print(f"✅ Loaded {len(players)} players")

    # Mark All-Stars
    mark_allstar_players(players)

    # Optimize
    lineup = simple_showdown_optimize(players)

    # Display
    display_final_lineup(lineup)

if __name__ == "__main__":
    main()
