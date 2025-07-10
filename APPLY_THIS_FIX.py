#!/usr/bin/env python3
"""
RECENT FORM INTEGRATION FIX
==========================
Apply this patch to core/dfs_optimizer.py (formerly bulletproof_dfs_core.py)
"""

# Add this method to the BulletproofDFSCore class:

def apply_recent_form_adjustments(self):
    """Apply recent form adjustments to all eligible players"""
    if not hasattr(self, 'form_analyzer') or not self.form_analyzer:
        print("⚠️ Form analyzer not initialized")
        return 0

    print("\n📊 APPLYING RECENT FORM ADJUSTMENTS...")

    eligible = [p for p in self.players if p.is_eligible_for_selection(self.optimization_mode)]
    adjusted_count = 0

    for player in eligible:
        try:
            # Get current enhanced score
            original_score = player.enhanced_score

            # Analyze form
            form_data = self.form_analyzer.analyze_player_form(player)

            if form_data and 'form_score' in form_data:
                # Apply multiplier
                player.enhanced_score = original_score * form_data['form_score']

                # Store form data
                player.recent_form = {
                    'status': 'hot' if form_data['form_score'] > 1.05 else 'cold' if form_data['form_score'] < 0.95 else 'normal',
                    'multiplier': form_data['form_score'],
                    'original_score': original_score,
                    'adjusted_score': player.enhanced_score
                }

                adjusted_count += 1

        except Exception as e:
            print(f"⚠️ Error applying form to {player.name}: {e}")

    print(f"✅ Form adjustments applied to {adjusted_count}/{len(eligible)} players")
    return adjusted_count

# IMPORTANT: Add this line to the enrich_players() method after other enrichments:
# adjusted = self.apply_recent_form_adjustments()
