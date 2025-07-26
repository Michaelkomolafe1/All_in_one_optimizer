from unified_player_model import UnifiedPlayer

# Create a test player with CORRECT parameters
try:
    player = UnifiedPlayer(
        id="test123",
        name="Test Player",
        team="NYY",
        salary=5000,
        primary_position="OF",
        positions=["OF"],  # List of positions
        base_projection=10.0
    )
    print("✅ Player created successfully!")
    
    # Check new attributes exist
    new_attributes = [
        'projected_ownership',
        'ownership_leverage', 
        'ownership_tier',
        'recent_form_score',
        'recent_game_logs',
        'opposing_pitcher_era',
        'opposing_pitcher_k9',
        'opp_pitcher_k_rate',
        'xwoba_diff',
        'is_undervalued',
        'platoon_advantage',
        'k9',
        'whiff_rate',
        'barrel_rate_against'
    ]

    print("\n🔍 Checking Player Model Updates:")
    print("-" * 40)

    missing = []
    for attr in new_attributes:
        if hasattr(player, attr):
            value = getattr(player, attr)
            print(f"✅ {attr}: {value}")
        else:
            print(f"❌ {attr}: MISSING")
            missing.append(attr)

    if missing:
        print(f"\n⚠️  Add these attributes to __init__ in unified_player_model.py:")
        print("-" * 60)
        print("\n# Add these lines to the __init__ method:\n")
        
        print("# Ownership projections (NEW)")
        print("self.projected_ownership = 0.0")
        print("self.ownership_leverage = 1.0")
        print('self.ownership_tier = "medium"')
        
        print("\n# Recent form data (NEW)")
        print("self.recent_form_score = 0.0")
        print("self.recent_game_logs = []")
        
        print("\n# Pitcher opponent data (NEW)")
        print("self.opposing_pitcher_era = 4.50")
        print("self.opposing_pitcher_k9 = 8.0")
        print("self.opp_pitcher_k_rate = 0.20")
        
        print("\n# Advanced stats (NEW)")
        print("self.xwoba_diff = 0.0")
        print("self.is_undervalued = False")
        print("self.platoon_advantage = False")
        
        print("\n# For pitchers (NEW)")
        print("self.k9 = 8.0")
        print("self.whiff_rate = 25.0")
        print("self.barrel_rate_against = 8.0")
    else:
        print("\n✅ All attributes added successfully!")
        
except Exception as e:
    print(f"❌ Error creating player: {e}")
    import traceback
    traceback.print_exc()
