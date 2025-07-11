#!/usr/bin/env python3
"""
DATA VALIDATOR - Comprehensive Input Validation for DFS Optimizer
================================================================
Prevents bad data from breaking calculations and provides data quality scores.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cleaned_data: Optional[Any] = None
    quality_score: float = 1.0  # 0-1 score indicating data quality


@dataclass 
class ValidationRules:
    """Configurable validation rules"""

    # Player data rules - will be populated from CSV
    player_rules: Dict[str, Any] = field(default_factory=lambda: {
        'salary': {'min': 2000, 'max': 15000},  # Will be updated dynamically
        'projection': {'min': 0, 'max': 60},
        'ownership': {'min': 0, 'max': 100},
        'name': {'min_length': 2, 'max_length': 50},
        'team': {'valid_teams': ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 
                                  'COL', 'DET', 'HOU', 'KC', 'LAA', 'LAD', 'MIA', 'MIL',
                                  'MIN', 'NYM', 'NYY', 'OAK', 'PHI', 'PIT', 'SD', 'SF',
                                  'SEA', 'STL', 'TB', 'TEX', 'TOR', 'WSH']},
        'positions': {'valid_positions': ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'UTIL', 'CPT']}
    })

    # Vegas data rules
    vegas_rules: Dict[str, Any] = field(default_factory=lambda: {
        'implied_total': {'min': 2.0, 'max': 15.0},
        'game_total': {'min': 5.0, 'max': 20.0},
        'moneyline': {'min': -500, 'max': 500},
        'spread': {'min': -10, 'max': 10}
    })

    # Statcast data rules
    statcast_rules: Dict[str, Any] = field(default_factory=lambda: {
        'barrel_rate': {'min': 0, 'max': 100},
        'hard_hit_rate': {'min': 0, 'max': 100},
        'k_rate': {'min': 0, 'max': 100},
        'walk_rate': {'min': 0, 'max': 100},
        'whip': {'min': 0, 'max': 5},
        'era': {'min': 0, 'max': 20},
        'xba': {'min': 0, 'max': 1},
        'xslg': {'min': 0, 'max': 4}
    })

    # Recent form rules
    form_rules: Dict[str, Any] = field(default_factory=lambda: {
        'games_required': 3,
        'max_games': 10,
        'score_range': {'min': -10, 'max': 60},
        'consistency_threshold': 0.3  # Max coefficient of variation
    })


class DataValidator:
    """Comprehensive data validation system"""

    def __init__(self, rules: Optional[ValidationRules] = None):
        """Initialize with validation rules"""
        self.rules = rules or ValidationRules()
        self._validation_cache = {}
        self._validation_stats = {
            'total_validations': 0,
            'failures': 0,
            'warnings': 0
        }

    def update_salary_range_from_players(self, players: List[Any]):
        """Dynamically update salary range from loaded players"""
        if not players:
            return

        salaries = [p.salary for p in players if hasattr(p, 'salary') and p.salary > 0]
        if salaries:
            import numpy as np
            self.rules.player_rules['salary'] = {
                'min': min(salaries),
                'max': max(salaries),
                'warn_low': np.percentile(salaries, 5),
                'warn_high': np.percentile(salaries, 95)
            }
            logger.info(f"Updated salary range: ${min(salaries)}-${max(salaries)}")

    def validate_player(self, player: Any) -> ValidationResult:
        """Validate all player data"""
        self._validation_stats['total_validations'] += 1

        errors = []
        warnings = []
        quality_score = 1.0

        # Basic attribute validation
        if not hasattr(player, 'name') or not player.name:
            errors.append("Player missing name")
            quality_score = 0
        else:
            # Name validation
            if len(player.name) < self.rules.player_rules['name']['min_length']:
                errors.append(f"Player name too short: {player.name}")
            elif len(player.name) > self.rules.player_rules['name']['max_length']:
                warnings.append(f"Player name unusually long: {player.name}")
                quality_score *= 0.95

        # Salary validation
        if hasattr(player, 'salary'):
            salary_rules = self.rules.player_rules['salary']
            salary_result = self._validate_range(
                player.salary, 
                salary_rules['min'],
                salary_rules['max'],
                "Salary"
            )
            errors.extend(salary_result.errors)
            warnings.extend(salary_result.warnings)

            # Check for unusually low/high salaries
            if 'warn_low' in salary_rules and player.salary < salary_rules['warn_low']:
                warnings.append(f"Unusually low salary: ${player.salary}")
                quality_score *= 0.95
            elif 'warn_high' in salary_rules and player.salary > salary_rules['warn_high']:
                warnings.append(f"Unusually high salary: ${player.salary}")
                quality_score *= 0.95

            quality_score *= salary_result.quality_score
        else:
            errors.append("Player missing salary")
            quality_score = 0

        # Projection validation
        for proj_attr in ['projection', 'base_projection', 'dff_projection', 'enhanced_score']:
            if hasattr(player, proj_attr):
                value = getattr(player, proj_attr)
                if value is not None:
                    proj_result = self._validate_range(
                        value,
                        self.rules.player_rules['projection']['min'],
                        self.rules.player_rules['projection']['max'],
                        f"{proj_attr}"
                    )
                    if proj_result.errors:
                        errors.extend(proj_result.errors)
                        quality_score *= 0.8
                    warnings.extend(proj_result.warnings)

        # Team validation
        if hasattr(player, 'team') and player.team:
            if player.team not in self.rules.player_rules['team']['valid_teams']:
                errors.append(f"Invalid team: {player.team}")
                quality_score *= 0.5

        # Position validation
        if hasattr(player, 'positions') and player.positions:
            invalid_positions = [
                pos for pos in player.positions 
                if pos not in self.rules.player_rules['positions']['valid_positions']
            ]
            if invalid_positions:
                errors.append(f"Invalid positions: {invalid_positions}")
                quality_score *= 0.7

        # Advanced data validation
        if hasattr(player, '_vegas_data') and player._vegas_data:
            vegas_result = self.validate_vegas_data(player._vegas_data)
            errors.extend(vegas_result.errors)
            warnings.extend(vegas_result.warnings)
            quality_score *= vegas_result.quality_score

        if hasattr(player, '_statcast_data') and player._statcast_data:
            statcast_result = self.validate_statcast_data(player._statcast_data)
            errors.extend(statcast_result.errors)
            warnings.extend(statcast_result.warnings)
            quality_score *= statcast_result.quality_score

        # Update stats
        if errors:
            self._validation_stats['failures'] += 1
        if warnings:
            self._validation_stats['warnings'] += 1

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0, min(1, quality_score))
        )

    def validate_vegas_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate Vegas betting data"""
        errors = []
        warnings = []
        quality_score = 1.0
        cleaned_data = data.copy()

        # Implied total validation
        if 'implied_total' in data:
            result = self._validate_range(
                data['implied_total'],
                self.rules.vegas_rules['implied_total']['min'],
                self.rules.vegas_rules['implied_total']['max'],
                "Implied total"
            )
            if result.errors:
                errors.extend(result.errors)
                # Try to fix if possible
                if data['implied_total'] > self.rules.vegas_rules['implied_total']['max']:
                    cleaned_data['implied_total'] = self.rules.vegas_rules['implied_total']['max']
                    warnings.append(f"Capped implied total from {data['implied_total']} to {cleaned_data['implied_total']}")
            quality_score *= result.quality_score

        # Game total validation
        if 'game_total' in data:
            result = self._validate_range(
                data['game_total'],
                self.rules.vegas_rules['game_total']['min'],
                self.rules.vegas_rules['game_total']['max'],
                "Game total"
            )
            errors.extend(result.errors)
            warnings.extend(result.warnings)
            quality_score *= result.quality_score

        # Cross-validation
        if 'implied_total' in data and 'opponent_total' in data:
            game_total_calc = data['implied_total'] + data['opponent_total']
            if 'game_total' in data:
                if abs(game_total_calc - data['game_total']) > 0.5:
                    warnings.append(f"Game total mismatch: {data['game_total']} vs calculated {game_total_calc:.1f}")
                    quality_score *= 0.9

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data if not errors else None,
            quality_score=quality_score
        )

    def validate_statcast_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate Statcast statistical data"""
        errors = []
        warnings = []
        quality_score = 1.0

        for metric, value in data.items():
            if metric in self.rules.statcast_rules:
                rule = self.rules.statcast_rules[metric]
                result = self._validate_range(
                    value,
                    rule['min'],
                    rule['max'],
                    metric
                )
                errors.extend(result.errors)
                warnings.extend(result.warnings)
                quality_score *= result.quality_score

        # Check for suspicious combinations
        if 'k_rate' in data and 'walk_rate' in data:
            if data['k_rate'] > 30 and data['walk_rate'] > 15:
                warnings.append("Unusual combination of high K rate and high walk rate")
                quality_score *= 0.95

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score
        )

    def validate_lineup(self, lineup: List[Any]) -> ValidationResult:
        """Validate a complete lineup"""
        errors = []
        warnings = []

        if not lineup:
            errors.append("Empty lineup")
            return ValidationResult(is_valid=False, errors=errors, quality_score=0)

        # Check lineup size
        if len(lineup) != 10:
            errors.append(f"Invalid lineup size: {len(lineup)} (expected 10)")

        # Check salary
        total_salary = sum(p.salary for p in lineup if hasattr(p, 'salary'))
        if total_salary > 50000:
            errors.append(f"Salary exceeds cap: ${total_salary}")
        elif total_salary < 47500:
            warnings.append(f"Low salary usage: ${total_salary} ({total_salary/500:.1f}%)")

        # Check positions
        positions_filled = {}
        for player in lineup:
            if hasattr(player, 'assigned_position'):
                pos = player.assigned_position
                positions_filled[pos] = positions_filled.get(pos, 0) + 1

        # Validate position requirements
        required = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        for pos, count in required.items():
            if positions_filled.get(pos, 0) != count:
                errors.append(f"Position {pos}: have {positions_filled.get(pos, 0)}, need {count}")

        # Check for duplicate players
        player_ids = [getattr(p, 'id', p.name) for p in lineup]
        if len(player_ids) != len(set(player_ids)):
            errors.append("Duplicate players in lineup")

        # Team exposure check
        team_counts = {}
        for player in lineup:
            if hasattr(player, 'team'):
                team_counts[player.team] = team_counts.get(player.team, 0) + 1

        for team, count in team_counts.items():
            if count > 4:
                warnings.append(f"High exposure to {team}: {count} players")

        quality_score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.05)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=max(0, quality_score)
        )

    def _validate_range(self, value: Union[int, float], 
                       min_val: Union[int, float], 
                       max_val: Union[int, float], 
                       field_name: str) -> ValidationResult:
        """Validate numeric range"""
        errors = []
        warnings = []
        quality_score = 1.0

        try:
            num_value = float(value)

            if num_value < min_val:
                errors.append(f"{field_name} too low: {num_value} < {min_val}")
                quality_score = 0
            elif num_value > max_val:
                errors.append(f"{field_name} too high: {num_value} > {max_val}")
                quality_score = 0
            elif num_value < min_val * 1.1:  # Within 10% of minimum
                warnings.append(f"{field_name} near minimum: {num_value}")
                quality_score = 0.9
            elif num_value > max_val * 0.9:  # Within 10% of maximum
                warnings.append(f"{field_name} near maximum: {num_value}")
                quality_score = 0.9

        except (TypeError, ValueError):
            errors.append(f"{field_name} is not a valid number: {value}")
            quality_score = 0

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score
        )

    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'total_validations': self._validation_stats['total_validations'],
            'failure_rate': self._validation_stats['failures'] / max(self._validation_stats['total_validations'], 1),
            'warning_rate': self._validation_stats['warnings'] / max(self._validation_stats['total_validations'], 1),
            'stats': self._validation_stats.copy()
        }


# Global validator instance
_validator_instance = None

def get_validator(rules: Optional[ValidationRules] = None) -> DataValidator:
    """Get or create global validator instance"""
    global _validator_instance

    if _validator_instance is None:
        _validator_instance = DataValidator(rules)
    elif rules is not None:
        _validator_instance.rules = rules

    return _validator_instance
