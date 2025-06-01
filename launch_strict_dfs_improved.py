#!/usr/bin/env python3
"""
Launch Strict DFS - Improved version with auto-detection
"""

import os
import sys
import glob
from pathlib import Path


def auto_detect_files():
    """Auto-detect your CSV files"""
    print("🔍 Auto-detecting your CSV files...")

    # Look for DraftKings files
    dk_patterns = ['DKSalaries*.csv', '*DKSalaries*.csv']
    dk_files = []
    for pattern in dk_patterns:
        dk_files.extend(glob.glob(pattern))

    # Look for DFF files
    dff_patterns = ['DFF*.csv', '*DFF*.csv', '*cheat*.csv']
    dff_files = []
    for pattern in dff_patterns:
        dff_files.extend(glob.glob(pattern))

    # Sort by modification time (newest first)
    dk_files.sort(key=os.path.getmtime, reverse=True)
    dff_files.sort(key=os.path.getmtime, reverse=True)

    dk_file = dk_files[0] if dk_files else None
    dff_file = dff_files[0] if dff_files else None

    print(f"📊 DraftKings file: {dk_file or 'Not found'}")
    print(f"🎯 DFF file: {dff_file or 'Not found'}")

    return dk_file, dff_file


def test_with_your_files():
    """Test the strict system with your actual files"""
    print("🧪 TESTING WITH YOUR ACTUAL FILES")
    print("=" * 50)

    dk_file, dff_file = auto_detect_files()

    if not dk_file:
        print("❌ No DraftKings CSV file found!")
        print("💡 Make sure DKSalaries.csv is in the current directory")
        return False

    try:
        from enhanced_strict_core import StrictDFSCore

        # Initialize the strict system
        dfs = StrictDFSCore()

        # Load your data
        print(f"📊 Loading DraftKings data from {Path(dk_file).name}...")
        success = dfs.load_draftkings_csv(dk_file)

        if not success:
            print("❌ Failed to load DraftKings data")
            return False

        print(f"✅ Loaded {len(dfs.players)} players")

        # Load DFF data if available
        if dff_file:
            print(f"🎯 Loading DFF data from {Path(dff_file).name}...")
            dfs.load_dff_data(dff_file)

        # Add your manual players
        manual_players = """CJ Abrams, James Wood, Nathaniel Lowe, Luis García Jr., Josh Bell, 
        Robert Hassell III, Keibert Ruiz, Jose Tena, Daylen Lile, Corbin Carroll, Ketel Marte, 
        Geraldo Perdomo, Josh Naylor, Eugenio Suárez, Lourdes Gurriel Jr., Gabriel Moreno, 
        Alek Thomas, Oneil Cruz, Andrew McCutchen, Bryan Reynolds, Spencer Horwitz, Henry Davis, 
        Ke'Bryan Hayes, Adam Frazier, Tommy Pham, Isiah Kiner-Falefa, Fernando Tatis Jr., 
        Luis Arraez, Manny Machado, Jackson Merrill, Gavin Sheets, Xander Bogaerts, 
        Jake Cronenworth, Tyler Wade, Elias Díaz, Byron Buxton, Trevor Larnach, Ryan Jeffers, 
        Carlos Correa, Brooks Lee, Ty France, Kody Clemens, Royce Lewis, Willi Castro, 
        J.P. Crawford, Jorge Polanco, Julio Rodríguez, Cal Raleigh, Randy Arozarena, 
        Rowdy Tellez, Leody Taveras, Miles Mastrobuoni, Ben Williamson, Shohei Ohtani, 
        Teoscar Hernández, Will Smith, Freddie Freeman, Andy Pages, Tommy Edman, 
        Kiké Hernández, Michael Conforto, Miguel Rojas"""

        print("🎯 Adding your manual player selections...")
        dfs.apply_manual_selection(manual_players)

        # Filter to ONLY confirmed + manual players
        print("🔒 Applying STRICT filtering (confirmed + manual ONLY)...")
        strict_players = dfs.get_strict_confirmed_players()

        print(f"✅ STRICT FILTER RESULT: {len(strict_players)} eligible players")

        # Verify no unconfirmed leaked through
        verification_passed = dfs.verify_no_unconfirmed_leaks(strict_players)

        if verification_passed:
            print("🎉 SUCCESS: No unconfirmed players found!")
            print("🔒 System is working perfectly!")
            return True
        else:
            print("❌ FAILED: Unconfirmed players detected!")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def launch_gui():
    """Launch the strict GUI"""
    print("🚀 Launching Strict DFS GUI...")

    try:
        import strict_dfs_gui
        return strict_dfs_gui.main()
    except ImportError:
        print("❌ strict_dfs_gui.py not found")
        print("💡 Run setup_strict_system.py first")
        return False
    except Exception as e:
        print(f"❌ GUI launch error: {e}")
        return False


def main():
    """Main launcher"""
    print("🚀 STRICT DFS SYSTEM LAUNCHER")
    print("=" * 50)
    print("🔒 Guarantees NO unconfirmed players in lineups")
    print("=" * 50)

    print("\nChoose an option:")
    print("1. 🧪 Test system with your CSV files")
    print("2. 🚀 Launch GUI")
    print("3. 📊 Show file detection")
    print("4. ❌ Exit")

    try:
        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            success = test_with_your_files()
            if success:
                print("\n🎉 Test passed! System ready for use.")
                launch_choice = input("Launch GUI now? (y/n): ").strip().lower()
                if launch_choice == 'y':
                    launch_gui()
            else:
                print("\n⚠️ Test failed. Check errors above.")

        elif choice == "2":
            launch_gui()

        elif choice == "3":
            auto_detect_files()

        elif choice == "4":
            print("👋 Goodbye!")

        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Launcher error: {e}")


if __name__ == "__main__":
    main()