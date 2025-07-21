#!/usr/bin/env python3
"""
SEARCH GUI CODE
===============
Find the exact location where you need to add game_info
"""

import os
import re


def search_gui_file():
    """Search through the GUI file and show relevant code sections"""
    print("\n🔍 SEARCHING YOUR GUI FILE FOR THE CODE LOCATION")
    print("=" * 70)

    gui_file = 'complete_dfs_gui_debug.py'

    if not os.path.exists(gui_file):
        print(f"❌ {gui_file} not found!")
        return

    with open(gui_file, 'r') as f:
        lines = f.readlines()

    print(f"✅ Loaded {gui_file} ({len(lines)} lines)")

    # First, find OptimizationWorker class
    print("\n📍 STEP 1: Finding OptimizationWorker class...")

    worker_start = None
    for i, line in enumerate(lines):
        if "class OptimizationWorker" in line:
            worker_start = i
            print(f"✅ Found at line {i + 1}")
            print(f"   {line.strip()}")
            break

    if worker_start is None:
        print("❌ Could not find OptimizationWorker class")
        print("\nSearching for alternative patterns...")

        # Try alternative searches
        for i, line in enumerate(lines):
            if "QThread" in line and "class" in line:
                print(f"\nFound QThread class at line {i + 1}:")
                print(f"   {line.strip()}")

    # Search for where players are created
    print("\n📍 STEP 2: Finding where players are created...")

    # Look for UnifiedPlayer creation
    player_creation_lines = []
    for i, line in enumerate(lines):
        if "UnifiedPlayer(" in line:
            player_creation_lines.append(i)
            print(f"\n✅ Found UnifiedPlayer creation at line {i + 1}")

            # Show context (10 lines before and after)
            start = max(0, i - 5)
            end = min(len(lines), i + 15)

            print("\n📄 CODE CONTEXT:")
            print("   Line | Code")
            print("   -----|-----")
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"   {j + 1:5d} {marker} {lines[j].rstrip()}")

    # Look for where we're iterating through rows
    print("\n📍 STEP 3: Finding DataFrame iteration...")

    for i, line in enumerate(lines):
        if "iterrows()" in line or "for idx, row in" in line:
            print(f"\n✅ Found DataFrame iteration at line {i + 1}")
            print(f"   {line.strip()}")

    # Look for display_position assignment
    print("\n📍 STEP 4: Finding display_position assignment...")

    display_pos_lines = []
    for i, line in enumerate(lines):
        if "display_position" in line:
            display_pos_lines.append(i)
            print(f"\n✅ Found display_position at line {i + 1}")

            # Show context
            start = max(0, i - 10)
            end = min(len(lines), i + 5)

            print("\n📄 THIS IS WHERE YOU NEED TO ADD game_info:")
            print("   Line | Code")
            print("   -----|-----")
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"   {j + 1:5d} {marker} {lines[j].rstrip()}")

            print(f"\n💡 ADD THESE LINES BEFORE LINE {i + 1}:")
            print("        player.opponent = row.get('Opponent', 'UNK')")
            print("        player.game_info = row.get('Game Info', '')  # CRITICAL!")

    # Search for the run method
    print("\n📍 STEP 5: Finding the run method...")

    for i, line in enumerate(lines):
        if "def run" in line and worker_start and i > worker_start:
            print(f"\n✅ Found run method at line {i + 1}")

            # Look for where players are processed
            for j in range(i, min(i + 100, len(lines))):
                if "row.get(" in lines[j]:
                    print(f"   Processing rows around line {j + 1}")

    # Summary
    print("\n\n" + "=" * 70)
    print("📋 SUMMARY - WHERE TO ADD THE CODE:")
    print("=" * 70)

    if display_pos_lines:
        line_num = display_pos_lines[0] + 1
        print(f"\n✅ Add the game_info assignment BEFORE line {line_num}")
        print(f"   (Before the display_position assignment)")

        print("\n📝 ADD THESE TWO LINES:")
        print("        player.opponent = row.get('Opponent', 'UNK')")
        print("        player.game_info = row.get('Game Info', '')")

    else:
        print("\n⚠️  Could not find display_position assignment")
        print("Look for where UnifiedPlayer is created and add:")
        print("   player.game_info = row.get('Game Info', '')")
        print("after the player is created")

    # Alternative search - look for gui_integration code
    print("\n\n📍 ALTERNATIVE: Checking if gui_integration.py code is used...")

    gui_integration_found = False
    for i, line in enumerate(lines):
        if "game_info = row.get('Game Info'" in line:
            gui_integration_found = True
            print(f"✅ game_info assignment already exists at line {i + 1}!")
            print(f"   {line.strip()}")
            break

    if gui_integration_found:
        print("\n✅ YOUR CODE ALREADY HAS game_info ASSIGNMENT!")
        print("The issue might be elsewhere.")


if __name__ == "__main__":
    search_gui_file()

    print("\n\n💡 NEXT STEPS:")
    print("1. Look at the line numbers shown above")
    print("2. Find where display_position is assigned")
    print("3. Add the two lines BEFORE that line")
    print("4. Save and restart your GUI")