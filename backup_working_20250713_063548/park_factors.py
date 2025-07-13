#!/usr/bin/env python3
"""
Park Factors Module for DFS Optimizer
=====================================
Provides park factor data for all MLB stadiums
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ParkFactors:
    """
    Park factors for MLB stadiums
    Higher values = hitter-friendly, lower = pitcher-friendly
    """

    # 2024 MLB Park Factors (based on 3-year averages)
    PARK_FACTORS = {
        # Extreme hitter-friendly
        "COL": {"factor": 1.20, "name": "Coors Field", "runs": 1.39, "hr": 1.37},

        # Hitter-friendly
        "CIN": {"factor": 1.12, "name": "Great American Ball Park", "runs": 1.18, "hr": 1.34},
        "TEX": {"factor": 1.10, "name": "Globe Life Field", "runs": 1.08, "hr": 1.15},
        "PHI": {"factor": 1.08, "name": "Citizens Bank Park", "runs": 1.06, "hr": 1.18},
        "MIL": {"factor": 1.06, "name": "American Family Field", "runs": 1.05, "hr": 1.13},
        "BAL": {"factor": 1.05, "name": "Camden Yards", "runs": 1.03, "hr": 1.25},
        "HOU": {"factor": 1.04, "name": "Minute Maid Park", "runs": 1.01, "hr": 1.10},
        "TOR": {"factor": 1.03, "name": "Rogers Centre", "runs": 1.02, "hr": 1.08},
        "BOS": {"factor": 1.03, "name": "Fenway Park", "runs": 1.04, "hr": 0.88},

        # Slight hitter-friendly
        "NYY": {"factor": 1.02, "name": "Yankee Stadium", "runs": 1.01, "hr": 1.15},
        "CHC": {"factor": 1.01, "name": "Wrigley Field", "runs": 1.00, "hr": 1.02},

        # Neutral
        "ARI": {"factor": 1.00, "name": "Chase Field", "runs": 1.00, "hr": 1.01},
        "ATL": {"factor": 1.00, "name": "Truist Park", "runs": 0.98, "hr": 1.02},
        "MIN": {"factor": 0.99, "name": "Target Field", "runs": 0.98, "hr": 0.95},

        # Slight pitcher-friendly
        "WSH": {"factor": 0.98, "name": "Nationals Park", "runs": 0.96, "hr": 0.92},
        "NYM": {"factor": 0.97, "name": "Citi Field", "runs": 0.95, "hr": 0.88},
        "LAA": {"factor": 0.96, "name": "Angel Stadium", "runs": 0.94, "hr": 0.91},
        "STL": {"factor": 0.95, "name": "Busch Stadium", "runs": 0.93, "hr": 0.85},
        "LAD": {"factor": 0.98, "name": "Dodger Stadium", "runs": 0.95, "hr": 0.92},
        "CHW": {"factor": 0.96, "name": "Guaranteed Rate Field", "runs": 0.94, "hr": 0.98},
        "CWS": {"factor": 0.96, "name": "Guaranteed Rate Field", "runs": 0.94, "hr": 0.98},  # Alias

        # Pitcher-friendly
        "CLE": {"factor": 0.94, "name": "Progressive Field", "runs": 0.92, "hr": 0.88},
        "TB": {"factor": 0.93, "name": "Tropicana Field", "runs": 0.91, "hr": 0.85},
        "KC": {"factor": 0.92, "name": "Kauffman Stadium", "runs": 0.91, "hr": 0.82},
        "DET": {"factor": 0.91, "name": "Comerica Park", "runs": 0.90, "hr": 0.78},
        "SEA": {"factor": 0.90, "name": "T-Mobile Park", "runs": 0.89, "hr": 0.80},

        # Extreme pitcher-friendly
        "OAK": {"factor": 0.89, "name": "Oakland Coliseum", "runs": 0.87, "hr": 0.75},
        "SF": {"factor": 0.88, "name": "Oracle Park", "runs": 0.87, "hr": 0.72},
        "SD": {"factor": 0.87, "name": "Petco Park", "runs": 0.86, "hr": 0.70},
        "MIA": {"factor": 0.86, "name": "loanDepot park", "runs": 0.85, "hr": 0.68},
        "PIT": {"factor": 0.85, "name": "PNC Park", "runs": 0.88, "hr": 0.73}
    }

    def __init__(self, custom_factors_file: Optional[str] = None):
        """
        Initialize park factors

        Args:
            custom_factors_file: Optional path to custom park factors JSON
        """
        self.factors = self.PARK_FACTORS.copy()

        # Load custom factors if provided
        if custom_factors_file and os.path.exists(custom_factors_file):
            try:
                with open(custom_factors_file, 'r') as f:
                    custom_factors = json.load(f)
                self.factors.update(custom_factors)
                logger.info(f"Loaded custom park factors from {custom_factors_file}")
            except Exception as e:
                logger.error(f"Error loading custom park factors: {e}")

    def get_factor(self, team_code: str) -> float:
        """
        Get park factor for a team

        Args:
            team_code: Team abbreviation (e.g., 'NYY', 'BOS')

        Returns:
            Park factor (1.0 = neutral)
        """
        if team_code in self.factors:
            return self.factors[team_code]['factor']

        logger.warning(f"No park factor found for {team_code}, using neutral (1.0)")
        return 1.0

    def get_detailed_factors(self, team_code: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed park factors including runs and home runs

        Args:
            team_code: Team abbreviation

        Returns:
            Dict with factor, runs, hr, and park name
        """
        return self.factors.get(team_code)

    def enrich_players(self, players: list) -> int:
        """
        Enrich players with park factor data

        Args:
            players: List of player objects

        Returns:
            Number of players enriched
        """
        enriched = 0

        for player in players:
            if hasattr(player, 'team') and player.team:
                park_data = self.get_detailed_factors(player.team)

                if park_data:
                    # Set park factors on player
                    player._park_factors = park_data

                    # Also set the simple factor for backward compatibility
                    player.park_factor = park_data['factor']

                    enriched += 1

                    # Log extreme parks
                    if park_data['factor'] >= 1.10:
                        logger.info(f"{player.name} plays in hitter-friendly {park_data['name']} "
                                    f"(factor: {park_data['factor']})")
                    elif park_data['factor'] <= 0.90:
                        logger.info(f"{player.name} plays in pitcher-friendly {park_data['name']} "
                                    f"(factor: {park_data['factor']})")

        return enriched

    def get_venue_factor(self, venue_name: str) -> float:
        """
        Get park factor by venue name (for games played at specific stadiums)

        Args:
            venue_name: Name of the stadium

        Returns:
            Park factor
        """
        # Search by stadium name
        for team_code, data in self.factors.items():
            if 'name' in data and data['name'].lower() in venue_name.lower():
                return data['factor']

        # Try to extract team from venue name
        venue_lower = venue_name.lower()
        for team_code, data in self.factors.items():
            if team_code.lower() in venue_lower:
                return data['factor']

        return 1.0  # Default neutral

    def print_summary(self):
        """Print park factors summary"""
        print("\n🏟️ MLB PARK FACTORS")
        print("=" * 60)

        # Sort by factor
        sorted_parks = sorted(
            self.factors.items(),
            key=lambda x: x[1]['factor'],
            reverse=True
        )

        print("\n🔥 Hitter-Friendly Parks:")
        print("-" * 40)
        for team, data in sorted_parks:
            if data['factor'] >= 1.05:
                print(f"{team:4} {data['name']:25} {data['factor']:.2f}")

        print("\n❄️ Pitcher-Friendly Parks:")
        print("-" * 40)
        for team, data in sorted_parks:
            if data['factor'] <= 0.95:
                print(f"{team:4} {data['name']:25} {data['factor']:.2f}")


# Global instance
_park_factors_instance = None


def get_park_factors(custom_file: Optional[str] = None) -> ParkFactors:
    """Get or create park factors instance"""
    global _park_factors_instance

    if _park_factors_instance is None:
        _park_factors_instance = ParkFactors(custom_file)

    return _park_factors_instance


# Integration with BulletproofDFSCore
def integrate_park_factors(core_instance):
    """
    Integrate park factors into BulletproofDFSCore

    Args:
        core_instance: Instance of BulletproofDFSCore
    """
    park_factors = get_park_factors()

    # Add to core
    core_instance.park_factors = park_factors

    # Add enrichment method
    def enrich_with_park_factors(self):
        """Enrich players with park factor data"""
        if hasattr(self, 'park_factors'):
            enriched = self.park_factors.enrich_players(self.players)
            print(f"🏟️ Park factors applied to {enriched} players")
            return enriched
        return 0

    # Bind method
    import types
    core_instance.enrich_with_park_factors = types.MethodType(
        enrich_with_park_factors,
        core_instance
    )

    print("✅ Park Factors integrated")


if __name__ == "__main__":
    # Test the module
    park_factors = get_park_factors()
    park_factors.print_summary()

    # Test specific lookups
    print("\n🧪 Test Lookups:")
    for team in ["COL", "SF", "NYY", "XYZ"]:
        factor = park_factors.get_factor(team)
        print(f"{team}: {factor}")