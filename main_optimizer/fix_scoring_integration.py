"""
FIX SCORING INTEGRATION
======================
Ensures scoring engine properly uses enrichments and calculates scores
"""


def fix_all_scoring_issues():
    """Apply all scoring fixes in the correct order"""

    from enhanced_scoring_engine import EnhancedScoringEngine
    from unified_core_system import UnifiedCoreSystem

    # Fix 1: Ensure scoring engine uses enrichments
    _orig_score_cash = EnhancedScoringEngine.score_player_cash
    _orig_score_gpp = EnhancedScoringEngine.score_player_gpp

    def new_score_player_cash(self, player):
        """Fixed cash scoring that uses enrichments"""
        # Get base projection - this is the issue!
        base = getattr(player, 'base_projection', 0)
        if base == 0:
            # Try alternate names
            base = getattr(player, 'dff_projection', 0)
            base = getattr(player, 'projection', 0) if base == 0 else base
            base = getattr(player, 'AvgPointsPerGame', 0) if base == 0 else base

        if base == 0:
            return 0

        score = base

        # Apply multipliers
        score *= getattr(player, 'recent_form', 1.0)
        score *= getattr(player, 'consistency_score', 1.0)
        score *= getattr(player, 'matchup_score', 1.0)
        score *= (1.0 + (getattr(player, 'park_factor', 1.0) - 1.0) * 0.3)
        score *= (1.0 + (getattr(player, 'weather_impact', 1.0) - 1.0) * 0.3)

        if player.is_pitcher:
            score *= 1.1

        return round(score, 2)

    def new_score_player_gpp(self, player):
        """Fixed GPP scoring that uses enrichments"""
        # Get base projection
        base = getattr(player, 'base_projection', 0)
        if base == 0:
            base = getattr(player, 'dff_projection', 0)
            base = getattr(player, 'projection', 0) if base == 0 else base
            base = getattr(player, 'AvgPointsPerGame', 0) if base == 0 else base

        if base == 0:
            return 0

        score = base

        # Vegas boost
        vegas_total = getattr(player, 'implied_team_score', getattr(player, 'team_total', 4.5))
        if vegas_total >= 5.5:
            score *= 1.25
        elif vegas_total >= 5.0:
            score *= 1.15
        elif vegas_total >= 4.5:
            score *= 1.05
        else:
            score *= 0.9

        # Environmental factors
        park = getattr(player, 'park_factor', 1.0)
        weather = getattr(player, 'weather_impact', 1.0)
        score *= (park * weather)

        # Batting order
        if not player.is_pitcher:
            bat_order = getattr(player, 'batting_order', 0)
            if bat_order and 1 <= bat_order <= 5:
                score *= 1.1

        return round(score, 2)

    # Apply the fixes
    EnhancedScoringEngine.score_player_cash = new_score_player_cash
    EnhancedScoringEngine.score_player_gpp = new_score_player_gpp

    # Fix 2: Ensure score_players actually stores the scores
    _orig_score_players = UnifiedCoreSystem.score_players

    def new_score_players(self, contest_type='gpp'):
        """Fixed scoring that stores optimization_score"""
        if not hasattr(self, 'scoring_engine'):
            from enhanced_scoring_engine import EnhancedScoringEngine
            self.scoring_engine = EnhancedScoringEngine()

        self.log(f"Scoring {len(self.player_pool)} players for {contest_type.upper()}")

        scored_count = 0
        zero_count = 0

        for player in self.player_pool:
            # Ensure we have base projection
            if not hasattr(player, 'base_projection') or player.base_projection == 0:
                # Try to find it from other fields
                player.base_projection = getattr(player, 'dff_projection',
                                                 getattr(player, 'projection',
                                                         getattr(player, 'AvgPointsPerGame', 0)))

            if contest_type.lower() == 'cash':
                score = self.scoring_engine.score_player_cash(player)
                player.cash_score = score
            else:
                score = self.scoring_engine.score_player_gpp(player)
                player.gpp_score = score

            player.optimization_score = score
            player.enhanced_score = score  # Also set this for compatibility

            if score > 0:
                scored_count += 1
            else:
                zero_count += 1

        self.log(f"Scored: {scored_count} players with scores > 0, {zero_count} with score = 0")

        if scored_count == 0:
            self.log("WARNING: All players have 0 score! Check base_projection field.", "error")

    UnifiedCoreSystem.score_players = new_score_players

    print("✅ All scoring fixes applied!")
    return True