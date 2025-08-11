#!/usr/bin/env python3
"""
DFS OPTIMIZER V2 - CLEAN MILP IMPLEMENTATION
============================================
Simple, working optimizer with no complex constraints
Lets scoring drive stacking behavior naturally
"""

import pulp
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    """Simple, clear configuration"""

    # Salary constraints
    salary_cap: int = 50000
    min_salary_cash: int = 47500  # 95% for cash
    min_salary_gpp: int = 45000  # 90% for GPP

    # Position requirements (DraftKings)
    positions: Dict[str, int] = None

    # Team constraints
    max_per_team_gpp: int = 5  # Allow natural stacking
    max_per_team_cash: int = 3  # Conservative for cash

    # Solver settings
    timeout_seconds: int = 30

    def __post_init__(self):
        if self.positions is None:
            self.positions = {
                'P': 2,  # 2 pitchers
                'C': 1,  # 1 catcher
                '1B': 1,  # 1 first base
                '2B': 1,  # 1 second base
                '3B': 1,  # 1 third base
                'SS': 1,  # 1 shortstop
                'OF': 3  # 3 outfielders
            }


class DFSOptimizer:
    """Clean, simple MILP optimizer"""

    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self.last_result = None

    # !/usr/bin/env python3
    """
    DFS OPTIMIZER V2 - CLEAN MILP IMPLEMENTATION
    ============================================
    Simple, working optimizer with no complex constraints
    Lets scoring drive stacking behavior naturally
    """

    import pulp
    from dataclasses import dataclass
    from typing import List, Dict, Tuple, Optional
    import logging

    logger = logging.getLogger(__name__)

    @dataclass
    class OptimizerConfig:
        """Simple, clear configuration"""

        # Salary constraints
        salary_cap: int = 50000
        min_salary_cash: int = 47500  # 95% for cash
        min_salary_gpp: int = 45000  # 90% for GPP

        # Position requirements (DraftKings)
        positions: Dict[str, int] = None

        # Team constraints
        max_per_team_gpp: int = 5  # Allow natural stacking
        max_per_team_cash: int = 3  # Conservative for cash

        # Solver settings
        timeout_seconds: int = 30

        def __post_init__(self):
            if self.positions is None:
                self.positions = {
                    'P': 2,  # 2 pitchers
                    'C': 1,  # 1 catcher
                    '1B': 1,  # 1 first base
                    '2B': 1,  # 1 second base
                    '3B': 1,  # 1 third base
                    'SS': 1,  # 1 shortstop
                    'OF': 3  # 3 outfielders
                }

    class DFSOptimizer:
        """Clean, simple MILP optimizer"""

        def __init__(self, config: Optional[OptimizerConfig] = None):
            self.config = config or OptimizerConfig()
            self.last_result = None

        def optimize(self,
                     players: List,
                     contest_type: str = 'gpp',
                     num_lineups: int = 1) -> List[Dict]:
            """
            Main optimization method

            Args:
                players: List of player objects with required attributes:
                    - name, position, team, salary, optimization_score
                contest_type: 'gpp' or 'cash'
                num_lineups: Number of lineups to generate

            Returns:
                List of lineup dictionaries
            """

            if not players:
                logger.error("No players to optimize")
                return []

            logger.info(f"Optimizing {contest_type} with {len(players)} players")

            lineups = []
            used_lineups = set()  # Track to ensure uniqueness

            for i in range(num_lineups):
                lineup = self._optimize_single(
                    players,
                    contest_type,
                    used_lineups
                )

                if lineup:
                    lineups.append(lineup)
                    # Add to used lineups (as frozen set of player names)
                    player_names = frozenset(p.name for p in lineup['players'])
                    used_lineups.add(player_names)
                else:
                    logger.warning(f"Could not generate lineup {i + 1}")
                    break

            return lineups

        def _optimize_single(self,
                             players: List,
                             contest_type: str,
                             exclude_lineups: set) -> Optional[Dict]:
            """Optimize a single lineup"""

            # Create problem
            prob = pulp.LpProblem("DFS_Lineup", pulp.LpMaximize)

            # Decision variables
            player_vars = pulp.LpVariable.dicts(
                "players",
                range(len(players)),
                cat="Binary"
            )

            # OBJECTIVE: Maximize total score
            prob += pulp.lpSum([
                players[i].optimization_score * player_vars[i]
                for i in range(len(players))
            ]), "Maximize_Score"

            # CONSTRAINT 1: Salary cap
            prob += pulp.lpSum([
                players[i].salary * player_vars[i]
                for i in range(len(players))
            ]) <= self.config.salary_cap, "Max_Salary"

            # CONSTRAINT 2: Minimum salary (based on contest type)
            min_salary = (self.config.min_salary_cash if contest_type == 'cash'
                          else self.config.min_salary_gpp)

            prob += pulp.lpSum([
                players[i].salary * player_vars[i]
                for i in range(len(players))
            ]) >= min_salary, "Min_Salary"

            # CONSTRAINT 3: Exactly 10 players
            prob += pulp.lpSum(player_vars.values()) == 10, "Roster_Size"

            # CONSTRAINT 4: Position requirements
            for position, required in self.config.positions.items():
                eligible = [i for i in range(len(players))
                            if self._player_eligible_for_position(players[i], position)]

                if len(eligible) < required:
                    logger.error(f"Not enough {position}: need {required}, have {len(eligible)}")
                    return None

                prob += pulp.lpSum([
                    player_vars[i] for i in eligible
                ]) == required, f"Position_{position}"

            # CONSTRAINT 5: Team limits (no forcing stacks!)
            max_per_team = (self.config.max_per_team_cash if contest_type == 'cash'
                            else self.config.max_per_team_gpp)

            teams = {}
            for i, player in enumerate(players):
                team = player.team
                if team not in teams:
                    teams[team] = []
                teams[team].append(i)

            for team, indices in teams.items():
                prob += pulp.lpSum([
                    player_vars[i] for i in indices
                ]) <= max_per_team, f"Team_Limit_{team}"

            # CONSTRAINT 6: Exclude previous lineups
            for used_lineup in exclude_lineups:
                # Find indices of players in this used lineup
                used_indices = [i for i, p in enumerate(players)
                                if p.name in used_lineup]

                if len(used_indices) == 10:
                    # Exclude this exact lineup
                    prob += pulp.lpSum([
                        player_vars[i] for i in used_indices
                    ]) <= 9, f"Exclude_Lineup_{len(exclude_lineups)}"

            # SOLVE
            try:
                solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.config.timeout_seconds)
                prob.solve(solver)

                if prob.status == pulp.LpStatusOptimal:
                    # Extract lineup
                    lineup_players = []
                    for i in range(len(players)):
                        if player_vars[i].varValue == 1:
                            lineup_players.append(players[i])

                    if len(lineup_players) != 10:
                        logger.error(f"Invalid lineup size: {len(lineup_players)}")
                        return None

                    # Calculate totals
                    total_salary = sum(p.salary for p in lineup_players)
                    total_score = sum(p.optimization_score for p in lineup_players)

                    # Count stacks
                    team_counts = {}
                    for p in lineup_players:
                        team = p.team
                        team_counts[team] = team_counts.get(team, 0) + 1

                    max_stack = max(team_counts.values()) if team_counts else 0

                    # Create result
                    return {
                        'players': lineup_players,
                        'salary': total_salary,
                        'projection': total_score,
                        'contest_type': contest_type,
                        'stack_info': team_counts,
                        'max_stack': max_stack
                    }

                else:
                    logger.warning(f"No optimal solution: {pulp.LpStatus[prob.status]}")
                    return None

            except Exception as e:
                logger.error(f"Optimization error: {e}")
                return None

        def _player_eligible_for_position(self, player, position: str) -> bool:
            """Check if player can fill a position"""

            # Get player's position(s)
            player_pos = player.position

            # Handle pitcher normalization
            if position == 'P':
                return player_pos in ['P', 'SP', 'RP']

            # Handle multi-position eligibility (e.g., "1B/3B")
            if '/' in player_pos:
                return position in player_pos.split('/')

            # Direct position match
            return player_pos == position

    # Simple test
    if __name__ == "__main__":
        print("DFS Optimizer V2 - Clean Implementation")
        print("=" * 50)

        # Create test players
        class TestPlayer:
            def __init__(self, name, pos, team, salary, score):
                self.name = name
                self.position = pos
                self.team = team
                self.salary = salary
                self.optimization_score = score

        # Test with simple slate
        test_players = [
            # Pitchers
            TestPlayer("Pitcher1", "P", "NYY", 9000, 45),
            TestPlayer("Pitcher2", "P", "BOS", 8000, 40),
            TestPlayer("Pitcher3", "P", "TB", 7000, 35),
            TestPlayer("Pitcher4", "P", "TOR", 6000, 30),

            # Catchers
            TestPlayer("Catcher1", "C", "NYY", 4000, 12),
            TestPlayer("Catcher2", "C", "BOS", 3500, 10),

            # Infielders
            TestPlayer("First1", "1B", "NYY", 5000, 15),
            TestPlayer("First2", "1B", "BOS", 4500, 13),
            TestPlayer("Second1", "2B", "NYY", 4000, 12),
            TestPlayer("Second2", "2B", "BOS", 3500, 10),
            TestPlayer("Third1", "3B", "NYY", 4500, 13),
            TestPlayer("Third2", "3B", "BOS", 4000, 11),
            TestPlayer("Short1", "SS", "NYY", 5000, 15),
            TestPlayer("Short2", "SS", "BOS", 4500, 13),

            # Outfielders
            TestPlayer("Out1", "OF", "NYY", 5500, 18),
            TestPlayer("Out2", "OF", "NYY", 5000, 16),
            TestPlayer("Out3", "OF", "BOS", 4500, 14),
            TestPlayer("Out4", "OF", "BOS", 4000, 12),
            TestPlayer("Out5", "OF", "TB", 3500, 10),
            TestPlayer("Out6", "OF", "TOR", 3000, 8),
        ]

        # Test optimization
        optimizer = DFSOptimizer()

        # Test GPP (should allow stacking)
        gpp_lineup = optimizer.optimize(test_players, 'gpp', 1)
        if gpp_lineup:
            lineup = gpp_lineup[0]
            print(f"GPP Lineup Generated!")
            print(f"  Salary: ${lineup['salary']:,}")
            print(f"  Score: {lineup['projection']:.1f}")
            print(f"  Max Stack: {lineup['max_stack']} players")
            print(f"  Teams: {lineup['stack_info']}")

        # Test Cash (should limit stacking)
        cash_lineup = optimizer.optimize(test_players, 'cash', 1)
        if cash_lineup:
            lineup = cash_lineup[0]
            print(f"\nCash Lineup Generated!")
            print(f"  Salary: ${lineup['salary']:,}")
            print(f"  Score: {lineup['projection']:.1f}")
            print(f"  Max Stack: {lineup['max_stack']} players")
            print(f"  Teams: {lineup['stack_info']}")

        print("\n✅ Optimizer V2 working correctly!")