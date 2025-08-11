#!/usr/bin/env python3
"""
MLB Park Factors for DFS Scoring
================================
Park factors affect scoring for both hitters and pitchers.
Values > 1.0 favor hitters, values < 1.0 favor pitchers.

Data based on historical run scoring environments and DFS performance.
"""

PARK_FACTORS = {
    # Extreme hitter-friendly
    "COL": {"factor": 1.20, "type": "extreme_hitter"},  # Coors Field - altitude effects

    # Hitter-friendly
    "CIN": {"factor": 1.12, "type": "hitter"},  # Great American Ball Park - small dimensions
    "TEX": {"factor": 1.10, "type": "hitter"},  # Globe Life Field - hitter friendly
    "PHI": {"factor": 1.08, "type": "hitter"},  # Citizens Bank Park - HR friendly
    "MIL": {"factor": 1.06, "type": "hitter"},  # American Family Field
    "BAL": {"factor": 1.05, "type": "hitter"},  # Camden Yards - HR friendly
    "HOU": {"factor": 1.04, "type": "hitter"},  # Minute Maid Park - Crawford Boxes
    "TOR": {"factor": 1.03, "type": "hitter"},  # Rogers Centre
    "BOS": {"factor": 1.03, "type": "hitter"},  # Fenway Park - Green Monster

    # Slight hitter-friendly
    "NYY": {"factor": 1.02, "type": "slight_hitter"},  # Yankee Stadium - short porch
    "CHC": {"factor": 1.01, "type": "slight_hitter"},  # Wrigley Field - wind dependent

    # Neutral parks
    "ARI": {"factor": 1.00, "type": "neutral"},  # Chase Field
    "ATL": {"factor": 1.00, "type": "neutral"},  # Truist Park
    "MIN": {"factor": 0.99, "type": "neutral"},  # Target Field

    # Slight pitcher-friendly
    "WSH": {"factor": 0.98, "type": "slight_pitcher"},  # Nationals Park
    "NYM": {"factor": 0.97, "type": "slight_pitcher"},  # Citi Field
    "LAA": {"factor": 0.96, "type": "slight_pitcher"},  # Angel Stadium
    "STL": {"factor": 0.95, "type": "slight_pitcher"},  # Busch Stadium

    # Pitcher-friendly
    "CLE": {"factor": 0.94, "type": "pitcher"},  # Progressive Field
    "TB": {"factor": 0.93, "type": "pitcher"},  # Tropicana Field
    "KC": {"factor": 0.92, "type": "pitcher"},  # Kauffman Stadium - large OF
    "DET": {"factor": 0.91, "type": "pitcher"},  # Comerica Park - spacious
    "SEA": {"factor": 0.90, "type": "pitcher"},  # T-Mobile Park - marine layer

    # Extreme pitcher-friendly
    "OAK": {"factor": 0.89, "type": "extreme_pitcher"},  # Oakland Coliseum - foul territory
    "SF": {"factor": 0.88, "type": "extreme_pitcher"},  # Oracle Park - wind/marine layer
    "SD": {"factor": 0.87, "type": "extreme_pitcher"},  # Petco Park - spacious
    "MIA": {"factor": 0.86, "type": "extreme_pitcher"},  # loanDepot park - huge OF
    "PIT": {"factor": 0.85, "type": "extreme_pitcher"},  # PNC Park - spacious

    # Additional teams
    "LAD": {"factor": 0.98, "type": "slight_pitcher"},  # Dodger Stadium
    "CHW": {"factor": 0.96, "type": "slight_pitcher"},  # Guaranteed Rate Field
    "CWS": {"factor": 0.96, "type": "slight_pitcher"},  # Alias for CHW
}


def get_park_factors() -> dict:
    """Get all park factors"""
    return PARK_FACTORS


def get_park_factor(team: str) -> float:
    """
    Get park factor for a specific team.
    Returns 1.0 (neutral) if team not found.
    """
    return PARK_FACTORS.get(team, {}).get('factor', 1.0)


def get_park_type(team: str) -> str:
    """
    Get park type classification for a team.
    Returns 'neutral' if team not found.
    """
    return PARK_FACTORS.get(team, {}).get('type', 'neutral')


def get_parks_by_type(park_type: str) -> list:
    """Get all teams with a specific park type"""
    return [
        team for team, data in PARK_FACTORS.items()
        if data.get('type') == park_type
    ]


def get_hitter_friendly_parks(min_factor: float = 1.05) -> list:
    """Get parks that favor hitters above a threshold"""
    return [
        team for team, data in PARK_FACTORS.items()
        if data.get('factor', 1.0) >= min_factor
    ]


def get_pitcher_friendly_parks(max_factor: float = 0.95) -> list:
    """Get parks that favor pitchers below a threshold"""
    return [
        team for team, data in PARK_FACTORS.items()
        if data.get('factor', 1.0) <= max_factor
    ]


def apply_park_factor(score: float, team: str, is_pitcher: bool = False) -> float:
    """
    Apply park factor to a score.

    Args:
        score: Base fantasy score
        team: Team abbreviation
        is_pitcher: True if applying to pitcher (inverts factor)

    Returns:
        Adjusted score
    """
    factor = get_park_factor(team)

    if is_pitcher:
        # Invert factor for pitchers (pitcher-friendly = good for pitchers)
        factor = 2.0 - factor

    return score * factor


# Aliases for common team abbreviation variations
TEAM_ALIASES = {
    "CHW": "CWS",  # Chicago White Sox
    "KC": "KCR",  # Kansas City Royals
    "SD": "SDP",  # San Diego Padres
    "SF": "SFG",  # San Francisco Giants
    "TB": "TBR",  # Tampa Bay Rays
    "WSH": "WAS",  # Washington Nationals
}


def normalize_team(team: str) -> str:
    """Normalize team abbreviation"""
    team = team.upper()
    return TEAM_ALIASES.get(team, team)


if __name__ == "__main__":
    # Test the module
    print("MLB Park Factors loaded successfully!")
    print(f"\nTotal parks: {len(PARK_FACTORS)}")
    print(f"Hitter-friendly: {len(get_hitter_friendly_parks())}")
    print(f"Pitcher-friendly: {len(get_pitcher_friendly_parks())}")
    print(f"\nMost hitter-friendly: COL = {get_park_factor('COL')}")
    print(f"Most pitcher-friendly: PIT = {get_park_factor('PIT')}")


# Function for backward compatibility
def get_park_factor_adjustment(team: str) -> float:
    """Get park factor for a team (backward compatibility)"""
    team = team.upper()
    if team in PARK_FACTORS:
        return PARK_FACTORS[team]["factor"]
    return 1.0


class ParkFactors:
    """Park factors class for the optimizer"""

    def __init__(self):
        self.factors = PARK_FACTORS
        self.logger = None
        try:
            import logging
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"ParkFactors initialized with {len(self.factors)} stadiums")
        except:
            pass

    def get_park_factor(self, team: str) -> float:
        """Get park factor for a team"""
        team = team.upper()
        if team in self.factors:
            return self.factors[team]["factor"]

        # Try team aliases
        team_aliases = {
            'WSH': 'WAS',
            'SF': 'SFG',
            'SD': 'SDP',
            'KC': 'KCR',
            'TB': 'TBR',
            'CWS': 'CHW',
            'LA': 'LAD'
        }

        if team in team_aliases:
            alias = team_aliases[team]
            if alias in self.factors:
                return self.factors[alias]["factor"]

        # Default to neutral
        if self.logger:
            self.logger.debug(f"No park factor found for {team}, using 1.0")
        return 1.0

    def get_park_type(self, team: str) -> str:
        """Get park type for a team"""
        team = team.upper()
        if team in self.factors:
            return self.factors[team]["type"]
        return "neutral"

    def is_hitter_friendly(self, team: str) -> bool:
        """Check if park is hitter-friendly"""
        return self.get_park_factor(team) > 1.02

    def is_pitcher_friendly(self, team: str) -> bool:
        """Check if park is pitcher-friendly"""
        return self.get_park_factor(team) < 0.98
