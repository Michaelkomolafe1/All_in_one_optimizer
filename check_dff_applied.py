#!/usr/bin/env python3
"""Check if DFF data was applied to players"""

try:
    # Try to access the last optimization data
    import pickle
    import os
    
    print("🔍 Checking for DFF data on players...")
    print("="*50)
    
    # Check if we can find any player objects with DFF data
    from bulletproof_dfs_core import BulletproofDFSCore
    
    # Create a test core
    core = BulletproofDFSCore()
    
    # Load your DraftKings CSV
    if os.path.exists("DKSalaries(2).csv"):
        core.load_draftkings_csv("DKSalaries(2).csv")
        
        # Check a few players for DFF attributes
        print("\n📊 Checking players for DFF data:")
        checked = 0
        has_dff = 0
        
        for player in core.players[:20]:  # Check first 20 players
            checked += 1
            if hasattr(player, 'dff_projection') and player.dff_projection > 0:
                has_dff += 1
                print(f"✅ {player.name}: DFF projection = {player.dff_projection}")
            elif hasattr(player, 'dff_data') and player.dff_data:
                has_dff += 1
                print(f"✅ {player.name}: Has DFF data")
        
        print(f"\n📊 Summary: {has_dff}/{checked} players have DFF data")
        
        if has_dff == 0:
            print("❌ No DFF data found on players")
            print("\nPossible reasons:")
            print("1. DFF file wasn't applied during optimization")
            print("2. Player names didn't match")
            print("3. DFF file format wasn't recognized")
    else:
        print("❌ DraftKings CSV not found")
        
except Exception as e:
    print(f"❌ Error checking DFF: {e}")

# Also check the scoring engine
try:
    from unified_scoring_engine import get_scoring_engine
    engine = get_scoring_engine()
    
    print("\n📊 Scoring Engine Weights:")
    print(f"  DFF weight: {getattr(engine, 'dff_weight', 0)}")
    print(f"  Base projection weight: {getattr(engine, 'base_projection_weight', 0)}")
    
except Exception as e:
    print(f"❌ Error checking scoring engine: {e}")
