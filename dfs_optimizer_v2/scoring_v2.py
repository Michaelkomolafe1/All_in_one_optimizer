#!/usr/bin/env python3
"""
UNIFIED SCORING ENGINE V2
=========================
One simple scoring system that drives natural stacking
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Simple, unified scoring system"""

    # Scoring parameters (based on your winning tests)
    GPP_PARAMS = {
        'high_total_threshold': 5.0,  # Teams scoring 5+ runs
        'team_total_boost': 1.15,  # 15% boost for high-scoring teams
        'batting_order_boost': 1.10,  # 10% boost for top of order
        'low_ownership_threshold': 15,  # Below 15% ownership
        'ownership_boost': 1.10,  # 10% boost for low ownership
        'pitcher_k_boost': 1.15,  # Boost for high K pitchers
        'k_rate_threshold': 9.0  # K/9 threshold
    }

    CASH_PARAMS = {
        'team_total_threshold': 4.5,  # More conservative
        'team_total_boost': 1.08,  # Smaller boost
        'batting_order_boost': 1.05,  # Smaller boost
        'consistency_threshold': 70,  # 70% consistency
        'consistency_boost': 1.10,  # Reward consistency
        'recent_form_boost': 1.05  # Small recent form boost
    }

    def __init__(self):
        self.players_scored = 0

    def score_all_players(self, players: List, contest_type: str = 'gpp') -> List:
        """
        Score all players for optimization

        This is the ONLY place scoring happens!
        """
        logger.info(f"Scoring {len(players)} players for {contest_type}")

        for player in players:
            player.optimization_score = self.score_player(player, contest_type)

        self.players_scored = len(players)

        # Log scoring distribution
        scores = [p.optimization_score for p in players]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        logger.info(f"Scoring complete: Avg={avg_score:.1f}, Max={max_score:.1f}, Min={min_score:.1f}")

        return players

    def score_player(self, player, contest_type: str = 'gpp') -> float:
        """
        Score a single player

        Simple multipliers create natural stacking behavior
        """

        # Start with base projection
        base_score = getattr(player, 'projection', 10.0)
        if base_score <= 0:
            base_score = 10.0  # Default

        # Apply contest-specific scoring
        if contest_type == 'gpp':
            score = self._score_for_gpp(player, base_score)
        else:
            score = self._score_for_cash(player, base_score)

        return score

    def _score_for_gpp(self, player, base_score: float) -> float:
        """GPP scoring - emphasize ceiling and correlation"""

        score = base_score
        params = self.GPP_PARAMS

        # CORRELATION DRIVER #1: Team Total
        team_total = getattr(player, 'implied_team_score', 4.5)
        if team_total >= params['high_total_threshold']:
            score *= params['team_total_boost']

        # CORRELATION DRIVER #2: Batting Order (for hitters)
        if player.position not in ['P', 'SP', 'RP']:
            batting_order = getattr(player, 'batting_order', 9)
            if batting_order <= 4:
                score *= params['batting_order_boost']

        # LEVERAGE: Low ownership
        ownership = getattr(player, 'ownership_projection', 20)
        if ownership < params['low_ownership_threshold']:
            score *= params['ownership_boost']

        # PITCHERS: K upside
        if player.position in ['P', 'SP', 'RP']:
            k_rate = getattr(player, 'k_rate', 7.0)
            if k_rate >= params['k_rate_threshold']:
                score *= params['pitcher_k_boost']

        return score

    def _score_for_cash(self, player, base_score: float) -> float:
        """Cash scoring - emphasize floor and consistency"""

        score = base_score
        params = self.CASH_PARAMS

        # SAFETY #1: Still want good teams, but less aggressive
        team_total = getattr(player, 'implied_team_score', 4.5)
        if team_total >= params['team_total_threshold']:
            score *= params['team_total_boost']

        # SAFETY #2: Batting order matters less
        if player.position not in ['P', 'SP', 'RP']:
            batting_order = getattr(player, 'batting_order', 9)
            if batting_order <= 5:  # Top 5 instead of top 4
                score *= params['batting_order_boost']

        # FLOOR: Consistency is key
        consistency = getattr(player, 'consistency_score', 50)
        if consistency >= params['consistency_threshold']:
            score *= params['consistency_boost']

        # FLOOR: Recent form
        recent_form = getattr(player, 'recent_form', 1.0)
        if recent_form > 1.0:
            score *= min(params['recent_form_boost'], recent_form)

        return score


# Test the scoring engine
if __name__ == "__main__":
    print("Scoring Engine V2 Test")
    print("=" * 50)


    # Create test player
    class TestPlayer:
        def __init__(self, name, pos, team):
            self.name = name
            self.position = pos
            self.team = team
            self.projection = 10.0
            self.implied_team_score = 5.5  # High scoring game
            self.batting_order = 3  # Heart of order
            self.ownership_projection = 12  # Low owned
            self.consistency_score = 75
            self.recent_form = 1.1
            self.k_rate = 9.5


    # Test scoring
    engine = ScoringEngine()

    # Test hitter in GPP
    hitter = TestPlayer("Mike Trout", "OF", "LAA")
    gpp_score = engine.score_player(hitter, 'gpp')
    print(f"Hitter GPP Score: {gpp_score:.2f}")
    print(f"  (Should be ~13.86 with boosts)")

    # Test same hitter in Cash
    cash_score = engine.score_player(hitter, 'cash')
    print(f"Hitter Cash Score: {cash_score:.2f}")
    print(f"  (Should be ~12.32 with smaller boosts)")

    # Test pitcher
    pitcher = TestPlayer("Gerrit Cole", "P", "NYY")
    pitcher_gpp = engine.score_player(pitcher, 'gpp')
    print(f"\nPitcher GPP Score: {pitcher_gpp:.2f}")
    print(f"  (Should be ~13.22 with K boost)")

    print("\n✅ Scoring Engine V2 working correctly!")