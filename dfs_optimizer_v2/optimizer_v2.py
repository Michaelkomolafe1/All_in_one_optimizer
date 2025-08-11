#!/usr/bin/env python3
"""DFS OPTIMIZER V2 - CLEAN MILP IMPLEMENTATION"""

import pulp
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class OptimizerConfig:
    """Simple, clear configuration"""
    salary_cap: int = 50000
    min_salary_cash: int = 47500
    min_salary_gpp: int = 45000
    positions: Dict[str, int] = None
    max_per_team_gpp: int = 5
    max_per_team_cash: int = 3
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if self.positions is None:
            self.positions = {
                'P': 2, 'C': 1, '1B': 1, '2B': 1,
                '3B': 1, 'SS': 1, 'OF': 3
            }

class DFSOptimizer:
    """Clean, simple MILP optimizer"""
    
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self.last_result = None
        
    def optimize(self, players: List, contest_type: str = 'gpp', num_lineups: int = 1) -> List[Dict]:
        """Main optimization method"""
        if not players:
            logger.error("No players to optimize")
            return []
            
        logger.info(f"Optimizing {contest_type} with {len(players)} players")
        lineups = []
        used_lineups = set()
        
        for i in range(num_lineups):
            lineup = self._optimize_single(players, contest_type, used_lineups)
            if lineup:
                lineups.append(lineup)
                player_names = frozenset(p.name for p in lineup['players'])
                used_lineups.add(player_names)
            else:
                logger.warning(f"Could not generate lineup {i+1}")
                break
        return lineups
    
    def _optimize_single(self, players: List, contest_type: str, exclude_lineups: set) -> Optional[Dict]:
        """Optimize a single lineup"""
        prob = pulp.LpProblem("DFS_Lineup", pulp.LpMaximize)
        player_vars = pulp.LpVariable.dicts("players", range(len(players)), cat="Binary")
        
        # Objective
        prob += pulp.lpSum([players[i].optimization_score * player_vars[i] for i in range(len(players))])
        
        # Salary constraints
        prob += pulp.lpSum([players[i].salary * player_vars[i] for i in range(len(players))]) <= self.config.salary_cap
        min_salary = self.config.min_salary_cash if contest_type == 'cash' else self.config.min_salary_gpp
        prob += pulp.lpSum([players[i].salary * player_vars[i] for i in range(len(players))]) >= min_salary
        
        # Roster size
        prob += pulp.lpSum(player_vars.values()) == 10
        
        # Position requirements
        for position, required in self.config.positions.items():
            eligible = [i for i in range(len(players)) if self._player_eligible_for_position(players[i], position)]
            if len(eligible) < required:
                logger.error(f"Not enough {position}: need {required}, have {len(eligible)}")
                return None
            prob += pulp.lpSum([player_vars[i] for i in eligible]) == required
        
        # Team limits
        max_per_team = self.config.max_per_team_cash if contest_type == 'cash' else self.config.max_per_team_gpp
        teams = {}
        for i, player in enumerate(players):
            if player.team not in teams:
                teams[player.team] = []
            teams[player.team].append(i)
        
        for team, indices in teams.items():
            prob += pulp.lpSum([player_vars[i] for i in indices]) <= max_per_team
        
        # Solve
        try:
            solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
            prob.solve(solver)
            
            if prob.status == pulp.LpStatusOptimal:
                lineup_players = [players[i] for i in range(len(players)) if player_vars[i].varValue == 1]
                
                if len(lineup_players) != 10:
                    return None
                
                team_counts = {}
                for p in lineup_players:
                    team_counts[p.team] = team_counts.get(p.team, 0) + 1
                
                return {
                    'players': lineup_players,
                    'salary': sum(p.salary for p in lineup_players),
                    'projection': sum(p.optimization_score for p in lineup_players),
                    'contest_type': contest_type,
                    'stack_info': team_counts,
                    'max_stack': max(team_counts.values()) if team_counts else 0
                }
            else:
                logger.warning(f"No optimal solution: {pulp.LpStatus[prob.status]}")
                return None
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return None
    
    def _player_eligible_for_position(self, player, position: str) -> bool:
        """Check if player can fill a position"""
        player_pos = player.position
        if position == 'P':
            return player_pos in ['P', 'SP', 'RP']
        if '/' in player_pos:
            return position in player_pos.split('/')
        return player_pos == position

if __name__ == "__main__":
    print("Optimizer loaded with optimize() method!")
