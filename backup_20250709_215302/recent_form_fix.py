
# RECENT FORM FIX PATCH
# Add this to bulletproof_dfs_core.py in the enrich_players method

def apply_recent_form_enhancements(self):
    """Fixed method to properly apply recent form adjustments"""
    if not self.form_analyzer:
        print("⚠️ Recent form analyzer not initialized")
        return 0

    print("\n📊 APPLYING RECENT FORM ANALYSIS...")
    adjusted_count = 0

    # Get eligible players
    eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]

    # Process ALL players (no limit)
    for player in eligible:
        try:
            # Analyze form
            form_data = self.form_analyzer.analyze_player_form(player)

            if form_data and 'form_score' in form_data:
                # Apply form multiplier to enhanced score
                original_score = player.enhanced_score
                form_multiplier = form_data['form_score']

                # Apply the adjustment
                player.enhanced_score = original_score * form_multiplier

                # Store form data on player
                player.recent_form = {
                    'status': 'hot' if form_multiplier > 1.1 else 'cold' if form_multiplier < 0.9 else 'normal',
                    'multiplier': form_multiplier,
                    'trend': form_data.get('trend', 'stable'),
                    'games_analyzed': form_data.get('games_analyzed', 0)
                }

                adjusted_count += 1

                # Log significant adjustments
                if abs(form_multiplier - 1.0) > 0.1:
                    print(f"   {player.name}: {original_score:.1f} → {player.enhanced_score:.1f} ({form_multiplier:.2f}x)")

        except Exception as e:
            print(f"   ⚠️ Error processing {player.name}: {e}")
            continue

    print(f"✅ Recent form applied to {adjusted_count}/{len(eligible)} players")
    return adjusted_count

# Also ensure this is called in the main enrichment flow:
# In enrich_players method, add:
# self.apply_recent_form_enhancements()
