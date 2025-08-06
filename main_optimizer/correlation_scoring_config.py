#!/usr/bin/env python3
"""
CORRELATION SCORING CONFIG
==========================
Simple configuration for DFS optimization
"""


class CorrelationScoringConfig:
    """Basic DFS configuration settings"""

    def __init__(self):
        # Salary cap
        self.salary_cap = 50000

        # Lineup requirements
        self.roster_size = 10  # Standard DraftKings MLB

        # Position requirements (DraftKings Classic)
        self.position_requirements = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }

        # Stacking constraints
        self.max_players_per_team = 5  # Maximum for stacking
        self.max_opposing_hitters = 0  # Don't stack against your pitcher

        # Optimization settings
        self.min_salary_usage = 0.90  # Use at least 90% of cap
        self.max_salary_usage = 1.00  # Can use full cap

        # Contest-specific defaults
        self.contest_type = 'gpp'

    def set_contest_type(self, contest_type: str):
        """Adjust settings based on contest type"""
        self.contest_type = contest_type.lower()

        if contest_type.lower() == 'cash':
            # Cash game settings (more conservative)
            self.max_players_per_team = 3
            self.min_salary_usage = 0.95  # Use more of cap
        else:
            # GPP settings (more aggressive)
            self.max_players_per_team = 5
            self.min_salary_usage = 0.90  # More flexibility


# For backwards compatibility
class OptimizerConfig(CorrelationScoringConfig):
    """Alias for compatibility"""
    pass