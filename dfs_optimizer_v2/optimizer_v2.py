#!/usr/bin/env python3
"""
DFS OPTIMIZER V2 - CLEAN MILP IMPLEMENTATION
============================================
Simple, working optimizer with no complex constraints
"""

import pulp
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    salary_cap: int = 50000
    min_salary_cash: int = 47500
    min_salary_gpp: int = 45000
    max_per_team_gpp: int = 5
    max_per_team_cash: int = 3
    timeout_seconds: int = 30

    def __post_init__(self):
        self.positions = {
            'P': 2,
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3
        }


class DFSOptimizer:
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()

    def optimize(self,
                 players: List,
                 contest_type: str = 'gpp',
                 num_lineups: int = 1) -> List[Dict]:
        """Main optimization method"""
        if not players:
            logger.error("No players to optimize")
            return []

        lineups = []
        used_lineups = set()

        for _ in range(num_lineups):
            lineup = self._optimize_single(players, contest_type, used_lineups)
            if lineup:
                lineups.append(lineup)
                used_lineups.add(frozenset(p.name for p in lineup['players']))
            else:
                logger.warning("Could not generate lineup")
                break

        return lineups

    def _optimize_single(self, players, contest_type, exclude_lineups):
        """Run one MILP solve"""
        prob = pulp.LpProblem("DFS_Lineup", pulp.LpMaximize)

        player_vars = pulp.LpVariable.dicts("players", range(len(players)), cat="Binary")

        # Objective
        prob += pulp.lpSum([players[i].optimization_score * player_vars[i]
                            for i in range(len(players))])

        # Salary cap
        salary_cap = self.config.salary_cap
        prob += pulp.lpSum([players[i].salary * player_vars[i]
                            for i in range(len(players))]) <= salary_cap

        # Min salary
        min_salary = (self.config.min_salary_cash if contest_type == 'cash'
                      else self.config.min_salary_gpp)
        prob += pulp.lpSum([players[i].salary * player_vars[i]
                            for i in range(len(players))]) >= min_salary

        # Exactly 10 players
        prob += pulp.lpSum(player_vars.values()) == 10

        # Position requirements
        for pos, req in self.config.positions.items():
            eligible = [i for i, p in enumerate(players)
                        if self._eligible(p, pos)]
            if len(eligible) < req:
                return None
            prob += pulp.lpSum(player_vars[i] for i in eligible) == req

        # Team limits
        max_team = (self.config.max_per_team_cash if contest_type == 'cash'
                    else self.config.max_per_team_gpp)
        teams = {}
        for i, p in enumerate(players):
            teams.setdefault(p.team, []).append(i)
        for t, idxs in teams.items():
            prob += pulp.lpSum(player_vars[i] for i in idxs) <= max_team

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
        prob.solve(solver)

        if prob.status != pulp.LpStatusOptimal:
            return None

        lineup_players = [players[i] for i, v in player_vars.items()
                          if v.varValue == 1]
        if len(lineup_players) != 10:
            return None

        return {
            'players': lineup_players,
            'salary': sum(p.salary for p in lineup_players),
            'projection': sum(p.optimization_score for p in lineup_players),
            'contest_type': contest_type,
            'max_stack': max([sum(1 for p in lineup_players if p.team == t)
                              for t in set(p.team for p in lineup_players)]),
        }

    def _eligible(self, player, position: str) -> bool:
        """Check positional eligibility"""
        if position == 'P':
            # Accept P, SP, RP
            return player.position in {'P', 'SP', 'RP'}
        # Handle multi-position like "1B/OF"
        pos_str = player.position
        return position in pos_str.split('/') if '/' in pos_str else position == pos_str