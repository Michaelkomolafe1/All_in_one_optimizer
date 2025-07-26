#!/usr/bin/env python3
"""
Cash Game Optimization Configurations
====================================
Specific settings for different contest types
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ContestConfig:
    """Configuration for different contest types"""
    max_opposing_hitters: int
    min_salary_usage: float
    max_players_per_team: int
    prefer_confirmed: bool
    stack_settings: Dict[str, Any]
    weight_overrides: Dict[str, float]


# Contest-specific configurations
CONTEST_CONFIGS = {
    'cash': ContestConfig(
        max_opposing_hitters=0,  # Strict - no opposing hitters
        min_salary_usage=0.98,  # Use 98%+ of salary
        max_players_per_team=3,  # Limit exposure
        prefer_confirmed=True,  # Heavily prefer confirmed
        stack_settings={
            'min_stack_size': 1,
            'max_stack_size': 2,
            'stack_boost': 0.02
        },
        weight_overrides={
            'base': 0.40,  # Trust projections more
            'recent_form': 0.30,  # Consistency matters
            'vegas': 0.15,
            'matchup': 0.10,
            'park': 0.05
        }
    ),

    'gpp': ContestConfig(
        max_opposing_hitters=1,  # Allow 1 elite hitter
        min_salary_usage=0.95,  # More flexibility
        max_players_per_team=5,  # Allow bigger stacks
        prefer_confirmed=False,  # Less important
        stack_settings={
            'min_stack_size': 3,
            'max_stack_size': 5,
            'stack_boost': 0.05
        },
        weight_overrides={
            'base': 0.25,  # Less projection focus
            'recent_form': 0.20,
            'vegas': 0.25,  # Game environment matters
            'matchup': 0.20,  # Ceiling plays
            'park': 0.10
        }
    ),

    'balanced_gpp': ContestConfig(
        max_opposing_hitters=1,
        min_salary_usage=0.96,
        max_players_per_team=4,
        prefer_confirmed=True,
        stack_settings={
            'min_stack_size': 2,
            'max_stack_size': 4,
            'stack_boost': 0.03
        },
        weight_overrides={
            'base': 0.30,
            'recent_form': 0.25,
            'vegas': 0.20,
            'matchup': 0.15,
            'park': 0.10
        }
    )
}


def get_contest_config(contest_type: str) -> ContestConfig:
    """Get configuration for contest type"""
    return CONTEST_CONFIGS.get(contest_type, CONTEST_CONFIGS['balanced_gpp'])


def apply_contest_config(optimizer, contest_type: str):
    """Apply contest configuration to optimizer"""
    config = get_contest_config(contest_type)

    # Update optimizer settings
    optimizer.config.max_opposing_hitters = config.max_opposing_hitters
    optimizer.config.min_salary_usage = config.min_salary_usage
    optimizer.config.max_players_per_team = config.max_players_per_team

    return config


def get_contest_description(contest_type: str) -> str:
    """Get human-readable description of contest settings"""
    config = get_contest_config(contest_type)

    descriptions = {
        'cash': "Cash Game - Safe, consistent plays with minimal variance",
        'gpp': "GPP Tournament - High upside plays with big stacks",
        'balanced_gpp': "Balanced GPP - Mix of safety and upside"
    }

    desc = descriptions.get(contest_type, "Custom settings")
    desc += f"\n• Opposing hitters allowed: {config.max_opposing_hitters}"
    desc += f"\n• Min salary usage: {config.min_salary_usage * 100:.0f}%"
    desc += f"\n• Max players per team: {config.max_players_per_team}"
    desc += f"\n• Stack size: {config.stack_settings['min_stack_size']}-{config.stack_settings['max_stack_size']}"

    return desc


if __name__ == "__main__":
    print("📋 Contest Configurations")
    print("=" * 50)

    for contest_type in ['cash', 'gpp', 'balanced_gpp']:
        print(f"\n{contest_type.upper()}:")
        print(get_contest_description(contest_type))