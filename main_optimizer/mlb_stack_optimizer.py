#!/usr/bin/env python3
"""
MLB STACK OPTIMIZER - Based on Real Winning Data
================================================
56.7% of GPP winners use 5-man stacks
26.5% use 4-man stacks
83.2% total use 4-5 man stacks!
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class MLBStackOptimizer:
    """Optimize for proven MLB DFS stack patterns"""

    # Based on your data analysis
    WINNING_PATTERNS = {
        '5-3': 0.271,  # 27.1% of 5-stack wins
        '5-2': 0.336,  # 33.6% of 5-stack wins
        '5-1-1-1': 0.391,  # 39.1% of 5-stack wins (MOST COMMON!)
        '4-4': 0.186,  # 18.6% of 4-stack wins
        '4-3': 0.209,  # 20.9% of 4-stack wins
        '4-2': 0.372,  # 37.2% of 4-stack wins (MOST COMMON!)
        '4-1-1-1-1': 0.232  # 23.2% of 4-stack wins
    }

    def identify_stack_candidates(self, players: List) -> Dict:
        """Identify teams worth stacking based on Vegas totals"""

        teams = defaultdict(list)
        team_totals = {}

        for player in players:
            if player.position not in ['P', 'SP', 'RP']:  # Hitters only
                team = player.team
                teams[team].append(player)

                # Track team Vegas total
                if team not in team_totals:
                    team_totals[team] = getattr(player, 'implied_team_score', 4.5)

        # Rank teams by stack potential
        stack_candidates = []
        for team, team_players in teams.items():
            if len(team_players) >= 5:  # Need enough players
                batting_order_players = [
                    p for p in team_players
                    if hasattr(p, 'batting_order') and 1 <= p.batting_order <= 6
                ]

                if len(batting_order_players) >= 4:
                    stack_candidates.append({
                        'team': team,
                        'players': batting_order_players,
                        'vegas_total': team_totals[team],
                        'stack_score': team_totals[team] * len(batting_order_players)
                    })

        # Sort by potential
        stack_candidates.sort(key=lambda x: x['stack_score'], reverse=True)

        return {
            'primary': stack_candidates[:3],  # Top 3 for primary
            'secondary': stack_candidates[3:8]  # Next 5 for secondary
        }

    def apply_stack_boost(self, players: List, strategy: str, contest_type: str) -> List:
        """Apply proven stack patterns to player scoring"""

        if contest_type.lower() != 'gpp':
            return players  # No stacking for cash

        # Identify stacks
        stacks = self.identify_stack_candidates(players)

        if not stacks['primary']:
            logger.warning("No viable stacks found!")
            return players

        # Choose pattern based on data
        import random
        pattern_choice = random.random()

        if pattern_choice < 0.567:  # 56.7% chance for 5-man
            primary_size = 5
            # Choose secondary based on 5-man data
            secondary_choice = random.random()
            if secondary_choice < 0.391:
                secondary_pattern = 'naked'  # 5-1-1-1
            elif secondary_choice < 0.727:
                secondary_pattern = '2-man'  # 5-2
            else:
                secondary_pattern = '3-man'  # 5-3
        else:  # 4-man stack
            primary_size = 4
            secondary_choice = random.random()
            if secondary_choice < 0.372:
                secondary_pattern = '2-man'  # 4-2
            elif secondary_choice < 0.604:
                secondary_pattern = 'naked'  # 4-1-1-1-1
            else:
                secondary_pattern = '3-man'  # 4-3

        # Apply boosts based on pattern
        primary_team = stacks['primary'][0]['team']

        for player in players:
            base_score = getattr(player, 'optimization_score', player.base_projection)

            # Primary stack boost
            if player.team == primary_team and player.position != 'P':
                order = getattr(player, 'batting_order', 99)
                if 1 <= order <= primary_size:
                    player.optimization_score = base_score * 1.5  # Massive boost
                    player.in_primary_stack = True
                    player.stack_pattern = f"{primary_size}-man primary"
                elif order <= 6:
                    player.optimization_score = base_score * 1.2  # Still good

            # Secondary stack boost
            elif secondary_pattern != 'naked' and len(stacks['primary']) > 1:
                secondary_team = stacks['primary'][1]['team']
                if player.team == secondary_team and player.position != 'P':
                    if secondary_pattern == '3-man':
                        if getattr(player, 'batting_order', 99) <= 3:
                            player.optimization_score = base_score * 1.25
                            player.in_secondary_stack = True
                    elif secondary_pattern == '2-man':
                        if getattr(player, 'batting_order', 99) <= 2:
                            player.optimization_score = base_score * 1.2
                            player.in_secondary_stack = True

            # Pitcher correlation
            if player.position in ['P', 'SP']:
                opponent = getattr(player, 'opponent', None)
                # Boost pitchers against low-scoring teams
                opp_total = 4.5  # Default
                for team_data in stacks['primary']:
                    if team_data['team'] == opponent:
                        opp_total = team_data['vegas_total']
                        break

                if opp_total < 4.0:
                    player.optimization_score = base_score * 1.15
                elif opp_total > 5.5:
                    player.optimization_score = base_score * 0.85  # Fade

        logger.info(f"Applied {primary_size}-man primary with {secondary_pattern} secondary pattern")

        return players