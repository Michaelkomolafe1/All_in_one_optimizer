@staticmethod
def _fix_scoring_display():
    """Fix scoring to store calculated values on player objects"""
    _orig_score_players = UnifiedCoreSystem.score_players

    def new_score_players(self, contest_type='gpp'):
        """Enhanced scoring that properly stores values"""
        if not hasattr(self, 'scoring_engine'):
            from enhanced_scoring_engine import EnhancedScoringEngine
            self.scoring_engine = EnhancedScoringEngine()

        # Use logger instead of self.log
        logger.info(f"Scoring {len(self.player_pool)} players for {contest_type.upper()}")

        score_distribution = {}
        scored_count = 0
        zero_count = 0

        for player in self.player_pool:
            # Ensure base projection exists
            if not hasattr(player, 'base_projection') or player.base_projection == 0:
                player.base_projection = getattr(player, 'dff_projection',
                                                 getattr(player, 'projection',
                                                         getattr(player, 'AvgPointsPerGame', 0)))

            # Calculate score based on contest type
            if contest_type.lower() == 'cash':
                score = self.scoring_engine.score_player_cash(player)
                player.cash_score = score
            else:
                score = self.scoring_engine.score_player_gpp(player)
                player.gpp_score = score

            # Store for optimization
            player.optimization_score = score
            player.enhanced_score = score

            # Track distribution
            if score > 0:
                scored_count += 1
                score_bucket = int(score)
                score_distribution[score_bucket] = score_distribution.get(score_bucket, 0) + 1
            else:
                zero_count += 1

        # Use logger instead of self.log
        logger.info(f"Scored: {scored_count} players with score > 0, {zero_count} with score = 0")

        if scored_count > 0:
            sorted_players = sorted(self.player_pool, key=lambda p: p.optimization_score, reverse=True)
            logger.info(f"Top scorer: {sorted_players[0].name} = {sorted_players[0].optimization_score:.1f}")
            logger.info(f"Bottom scorer: {sorted_players[-1].name} = {sorted_players[-1].optimization_score:.1f}")
        else:
            logger.warning("WARNING: All players have 0 score! Check projections.")

    UnifiedCoreSystem.score_players = new_score_players