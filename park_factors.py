#!/usr/bin/env python3
"""
Park Factors Module - Stadium effects on scoring
===============================================
Provides park factor data for all MLB stadiums
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ParkFactors:
    """
    Park factors for MLB stadiums based on historical run scoring
    """

    def __init__(self):
        # 2024 Park factors (1.0 = neutral, >1.0 = hitter friendly, <1.0 = pitcher friendly)
        self.park_factors = {
            # Extreme Hitter Parks
            'Coors Field': 1.15,  # COL - Altitude effects
            'Great American Ball Park': 1.10,  # CIN - Small dimensions
            'Globe Life Field': 1.08,  # TEX - Hitter friendly

            # Moderate Hitter Parks
            'Fenway Park': 1.06,  # BOS - Green Monster
            'Yankee Stadium': 1.05,  # NYY - Short porch
            'Citizens Bank Park': 1.05,  # PHI - Bandbox
            'Camden Yards': 1.04,  # BAL - HR friendly
            'American Family Field': 1.04,  # MIL - Good for power

            # Neutral Parks
            'Chase Field': 1.02,  # ARI - Controlled environment
            'Rogers Centre': 1.01,  # TOR - Dome
            'Truist Park': 1.00,  # ATL - Neutral
            'Busch Stadium': 1.00,  # STL - Balanced
            'Target Field': 0.99,  # MIN - Slightly pitcher friendly
            'Guaranteed Rate Field': 0.99,  # CHW - Balanced

            # Pitcher Parks
            'T-Mobile Park': 0.96,  # SEA - Marine layer
            'Citi Field': 0.95,  # NYM - Big dimensions
            'loanDepot park': 0.94,  # MIA - Spacious
            'Comerica Park': 0.94,  # DET - Deep fences
            'Petco Park': 0.93,  # SD - Marine layer + size
            'Oracle Park': 0.92,  # SF - Wind + marine layer
            'Kauffman Stadium': 0.92,  # KC - Huge outfield

            # Parks with unique factors
            'Tropicana Field': 0.98,  # TB - Dome, turf
            'Angel Stadium': 0.98,  # LAA - Neutral-ish
            'Dodger Stadium': 0.97,  # LAD - Pitcher friendly
            'Wrigley Field': 1.03,  # CHC - Wind dependent
            'Progressive Field': 0.98,  # CLE - Neutral
            'PNC Park': 0.97,  # PIT - Slightly pitcher friendly
            'Oakland Coliseum': 0.95,  # OAK - Foul territory
            'Nationals Park': 0.99,  # WSH - Neutral
            'Minute Maid Park': 1.03,  # HOU - Crawford boxes
        }

        # Team to stadium mapping
        self.team_stadiums = {
            'COL': 'Coors Field',
            'CIN': 'Great American Ball Park',
            'TEX': 'Globe Life Field',
            'BOS': 'Fenway Park',
            'NYY': 'Yankee Stadium',
            'PHI': 'Citizens Bank Park',
            'BAL': 'Camden Yards',
            'MIL': 'American Family Field',
            'ARI': 'Chase Field',
            'TOR': 'Rogers Centre',
            'ATL': 'Truist Park',
            'STL': 'Busch Stadium',
            'MIN': 'Target Field',
            'CHW': 'Guaranteed Rate Field',
            'SEA': 'T-Mobile Park',
            'NYM': 'Citi Field',
            'MIA': 'loanDepot park',
            'DET': 'Comerica Park',
            'SD': 'Petco Park',
            'SF': 'Oracle Park',
            'KC': 'Kauffman Stadium',
            'TB': 'Tropicana Field',
            'LAA': 'Angel Stadium',
            'LAD': 'Dodger Stadium',
            'CHC': 'Wrigley Field',
            'CLE': 'Progressive Field',
            'PIT': 'PNC Park',
            'OAK': 'Oakland Coliseum',
            'WSH': 'Nationals Park',
            'HOU': 'Minute Maid Park'
        }

    def get_park_factor(self, team: str, is_home: bool = True) -> float:
        """
        Get park factor for a team

        Args:
            team: Team code (e.g., 'COL', 'NYY')
            is_home: Whether the team is playing at home

        Returns:
            Park factor (1.0 = neutral)
        """
        if not is_home:
            # For away games, return neutral (park factor applies to home venue)
            return 1.0

        stadium = self.team_stadiums.get(team)
        if not stadium:
            logger.warning(f"No stadium found for team {team}")
            return 1.0

        return self.park_factors.get(stadium, 1.0)

    def enrich_players_with_park_factors(self, players: list) -> int:
        """
        Enrich players with park factor data

        Args:
            players: List of player objects

        Returns:
            Number of players enriched
        """
        enriched = 0

        for player in players:
            try:
                # Skip if no team
                if not hasattr(player, 'team') or not player.team:
                    continue

                # Determine if home game (you'd need game schedule data for this)
                # For now, assume home if player has is_home attribute
                is_home = getattr(player, 'is_home', True)

                # Get park factor
                factor = self.get_park_factor(player.team, is_home)

                # Apply to player
                player._park_factors = {
                    'factor': factor,
                    'stadium': self.team_stadiums.get(player.team, 'Unknown'),
                    'is_home': is_home
                }

                enriched += 1

                # Log extreme parks
                if factor >= 1.10:
                    logger.info(f"{player.name} playing at {player._park_factors['stadium']} (factor: {factor:.2f})")
                elif factor <= 0.93:
                    logger.info(f"{player.name} playing at {player._park_factors['stadium']} (factor: {factor:.2f})")

            except Exception as e:
                logger.debug(f"Error applying park factor to {getattr(player, 'name', 'unknown')}: {e}")

        return enriched

    def get_extreme_parks(self, threshold: float = 0.05) -> Dict[str, list]:
        """
        Get lists of extreme hitter/pitcher parks

        Args:
            threshold: Deviation from 1.0 to be considered extreme

        Returns:
            Dict with 'hitter' and 'pitcher' park lists
        """
        extreme_parks = {
            'hitter': [],
            'pitcher': []
        }

        for stadium, factor in self.park_factors.items():
            if factor >= 1.0 + threshold:
                extreme_parks['hitter'].append((stadium, factor))
            elif factor <= 1.0 - threshold:
                extreme_parks['pitcher'].append((stadium, factor))

        # Sort by factor
        extreme_parks['hitter'].sort(key=lambda x: x[1], reverse=True)
        extreme_parks['pitcher'].sort(key=lambda x: x[1])

        return extreme_parks

    def print_summary(self):
        """Print park factors summary"""
        print("\n🏟️ PARK FACTORS SUMMARY")
        print("=" * 50)

        extreme = self.get_extreme_parks()

        print("\n🔥 Hitter-Friendly Parks:")
        for stadium, factor in extreme['hitter'][:5]:
            team = [t for t, s in self.team_stadiums.items() if s == stadium][0]
            print(f"   {stadium} ({team}): {factor:.2f}")

        print("\n❄️ Pitcher-Friendly Parks:")
        for stadium, factor in extreme['pitcher'][:5]:
            team = [t for t, s in self.team_stadiums.items() if s == stadium][0]
            print(f"   {stadium} ({team}): {factor:.2f}")


# Global instance
_park_factors_instance = None


def get_park_factors() -> ParkFactors:
    """Get or create global park factors instance"""
    global _park_factors_instance

    if _park_factors_instance is None:
        _park_factors_instance = ParkFactors()

    return _park_factors_instance


# Integration with BulletproofDFSCore
def enrich_players_with_park_factors(core_instance, players: list) -> int:
    """
    Helper function to enrich players with park factors
    Used by BulletproofDFSCore
    """
    park_factors = get_park_factors()
    return park_factors.enrich_players_with_park_factors(players)


if __name__ == "__main__":
    # Test the module
    pf = ParkFactors()
    pf.print_summary()

    # Test specific parks
    print("\n\nTest specific teams:")
    for team in ['COL', 'SF', 'NYY', 'SD']:
        factor = pf.get_park_factor(team)
        stadium = pf.team_stadiums[team]
        print(f"{team} at {stadium}: {factor:.2f}")