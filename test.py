#!/usr/bin/env python3
"""
Ultimate MLB DFS Scoring Test
Combines ALL methods from all tests to find the definitive best
"""
import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict
import json
from datetime import datetime


@dataclass
class MLBPlayer:
    """Complete MLB player model with all factors"""
    id: int
    name: str
    position: str
    salary: int
    team: str
    opponent: str

    # Core projections
    dk_projection: float
    base_projection: float  # Raw projection

    # Vegas
    vegas_total: float
    team_total: float
    spread: float

    # Historical performance
    recent_avg: float
    recent_ceiling: float
    recent_floor: float
    recent_consistency: float
    season_avg: float
    last_10_avg: float
    last_5_avg: float

    # Baseball specific
    batting_order: int
    vs_pitcher_type: float  # vs L/R
    park_factor: float
    weather_score: float
    is_home: bool

    # Pitcher specific
    is_pitcher: bool
    k_rate: float
    whip: float
    opposing_lineup_strength: float

    # Advanced metrics
    momentum_score: float
    platoon_advantage: float
    bullpen_quality: float  # Team's bullpen
    recent_form_trend: float  # Trending up/down

    # Data completeness tracking
    has_vegas: bool
    has_recent: bool
    has_matchup: bool
    has_batting_order: bool
    data_completeness: float

    # Other
    matchup_score: float
    ownership_proj: float

    # Hidden true performance
    true_skill: float
    actual_points: float = 0.0


class UltimateMLBTester:
    """Test ALL scoring methods comprehensively"""

    def __init__(self):
        self.salary_cap = 50000
        self.min_salary = 45000  # Lowered from 47000 to allow more flexibility

        # DraftKings MLB roster
        self.roster_positions = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

        # All scoring methods to test
        self.scoring_methods = [
            'pure_data',
            'dynamic',
            'enhanced_pure',
            'dk_only',
            'hybrid_smart',
            'recency_weighted',
            'season_long',
            'baseball_optimized',
            'bayesian',
            'correlation_aware',
            'weather_adjusted',
            'advanced_stack'
        ]

    def generate_realistic_slate(self, slate_size: str = 'main') -> List[MLBPlayer]:
        """Generate realistic MLB slate with varying data completeness"""

        # Slate configurations
        slate_configs = {
            'small': 4,  # 4 games (early slate)
            'medium': 7,  # 7 games (afternoon)
            'main': 10,  # 10 games (main slate)
            'large': 15  # 15 games (all day)
        }

        num_games = slate_configs.get(slate_size, 10)
        players = []
        player_id = 0

        for game_id in range(num_games):
            # Game environment
            vegas_total = np.random.normal(8.5, 1.5)
            weather = np.random.uniform(0.7, 1.0)
            park_factor = np.random.uniform(0.85, 1.15)

            for team_side in range(2):
                is_home = team_side == 0
                team_total = vegas_total / 2 + np.random.normal(0, 0.5)

                # Generate starting pitcher
                pitcher = self.generate_pitcher(
                    player_id, game_id, team_side,
                    vegas_total, team_total, weather, park_factor, is_home
                )
                players.append(pitcher)
                player_id += 1

                # Generate lineup
                positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'OF']
                batting_order = 1

                for pos in positions:
                    # Always generate all positions to ensure enough players
                    hitter = self.generate_hitter(
                        player_id, pos, game_id, team_side,
                        batting_order, vegas_total, team_total,
                        weather, park_factor, is_home
                    )
                    players.append(hitter)
                    player_id += 1
                    batting_order += 1

        # Add some extra cheap players to ensure buildable lineups
        # Add cheap pitchers
        for i in range(max(2, num_games // 3)):
            cheap_pitcher = self.generate_cheap_player(player_id, 'P', is_pitcher=True)
            players.append(cheap_pitcher)
            player_id += 1

        # Add cheap position players
        for pos in ['C', 'SS', '2B']:  # Typically scarce positions
            for i in range(max(2, num_games // 4)):
                cheap_player = self.generate_cheap_player(player_id, pos, is_pitcher=False)
                players.append(cheap_player)
                player_id += 1

        return players

        return player

    def generate_cheap_player(self, player_id: int, position: str, is_pitcher: bool) -> MLBPlayer:
        """Generate cheap filler players to ensure lineups can be built"""
        if is_pitcher:
            salary = np.random.randint(4000, 5500)
            true_skill = 0.5 + np.random.normal(0, 0.1)
            dk_projection = 8 + true_skill * 3
        else:
            salary = np.random.randint(2000, 3500)
            true_skill = 0.4 + np.random.normal(0, 0.1)
            dk_projection = 5 + true_skill * 2

        salary = round(salary / 100) * 100

        # Minimal data for cheap players
        has_recent = np.random.random() < 0.5
        recent_avg = dk_projection * 0.8 if has_recent else 0

        return MLBPlayer(
            id=player_id,
            name=f"CHEAP_{position}{player_id}",
            position=position,
            salary=salary,
            team=f"TM{np.random.randint(0, 30)}",
            opponent=f"TM{np.random.randint(0, 30)}",
            dk_projection=dk_projection,
            base_projection=dk_projection * 0.9,
            vegas_total=0,
            team_total=0,
            spread=0,
            recent_avg=recent_avg,
            recent_ceiling=recent_avg * 1.5 if has_recent else 0,
            recent_floor=recent_avg * 0.5 if has_recent else 0,
            recent_consistency=0.5,
            season_avg=dk_projection * 0.85,
            last_10_avg=dk_projection * 0.85,
            last_5_avg=recent_avg,
            batting_order=9 if not is_pitcher else 0,
            vs_pitcher_type=1.0,
            park_factor=1.0,
            weather_score=1.0,
            is_home=np.random.random() > 0.5,
            is_pitcher=is_pitcher,
            k_rate=0.15 if is_pitcher else 0,
            whip=1.4 if is_pitcher else 0,
            opposing_lineup_strength=1.0,
            momentum_score=1.0,
            platoon_advantage=1.0,
            bullpen_quality=1.0,
            recent_form_trend=0,
            has_vegas=False,
            has_recent=has_recent,
            has_matchup=False,
            has_batting_order=not is_pitcher,
            data_completeness=0.25,
            matchup_score=dk_projection * 0.9,
            ownership_proj=np.random.uniform(1, 5),
            true_skill=true_skill,
            actual_points=0
        )



    def generate_pitcher(self, player_id: int, game_id: int, team_side: int,
                         vegas_total: float, team_total: float, weather: float,
                         park_factor: float, is_home: bool) -> MLBPlayer:
        """Generate pitcher with realistic attributes"""

        # Ace vs average pitcher
        is_ace = np.random.random() < 0.2

        # Ensure some cheap pitchers
        if np.random.random() < 0.1:  # 10% chance of cheap pitcher
            salary = np.random.randint(4000, 5500)
            true_skill = 0.6 + np.random.normal(0, 0.15)
            k_rate = 0.15 + np.random.normal(0, 0.03)
        elif is_ace:
            salary = np.random.randint(8500, 11500)
            true_skill = 1.2 + np.random.normal(0, 0.2)
            k_rate = 0.25 + np.random.normal(0, 0.05)
        else:
            salary = np.random.randint(5500, 8500)
            true_skill = 0.8 + np.random.normal(0, 0.2)
            k_rate = 0.18 + np.random.normal(0, 0.05)

        salary = round(salary / 100) * 100

        # Base projection
        dk_projection = 15 + (salary - 5500) / 500 * 2
        dk_projection *= true_skill

        # Data completeness (70% have all data)
        has_full_data = np.random.random() < 0.7

        if has_full_data:
            has_vegas = True
            has_recent = True
            has_matchup = True
        else:
            has_vegas = np.random.random() < 0.8
            has_recent = np.random.random() < 0.9
            has_matchup = np.random.random() < 0.7

        # Historical performance
        recent_games = []
        for i in range(10):
            # Pitchers have high variance
            game_score = dk_projection * np.random.normal(1.0, 0.4)
            game_score = max(-10, min(60, game_score))
            recent_games.append(game_score)

        recent_5 = recent_games[:5]

        # Trending
        trend = (np.mean(recent_5) - np.mean(recent_games[5:])) / (np.mean(recent_games) + 1)

        return MLBPlayer(
            id=player_id,
            name=f"P{player_id}",
            position='P',
            salary=salary,
            team=f"TM{team_side}",
            opponent=f"TM{1 - team_side}",
            dk_projection=dk_projection,
            base_projection=dk_projection * 0.9,
            vegas_total=vegas_total if has_vegas else 0,
            team_total=team_total if has_vegas else 0,
            spread=np.random.normal(0, 1.5) if has_vegas else 0,
            recent_avg=np.mean(recent_games) if has_recent else 0,
            recent_ceiling=max(recent_games) if has_recent else 0,
            recent_floor=min(recent_games) if has_recent else 0,
            recent_consistency=1 - np.std(recent_games) / (np.mean(recent_games) + 1) if has_recent else 0,
            season_avg=np.mean(recent_games) * 0.95,
            last_10_avg=np.mean(recent_games),
            last_5_avg=np.mean(recent_5) if has_recent else 0,
            batting_order=0,
            vs_pitcher_type=1.0,
            park_factor=park_factor,
            weather_score=weather,
            is_home=is_home,
            is_pitcher=True,
            k_rate=k_rate,
            whip=1.0 + (1.5 - true_skill) * 0.3,
            opposing_lineup_strength=0.8 + np.random.random() * 0.4,
            momentum_score=1.0 + trend,
            platoon_advantage=1.0,
            bullpen_quality=np.random.uniform(0.7, 1.3),
            recent_form_trend=trend,
            has_vegas=has_vegas,
            has_recent=has_recent,
            has_matchup=has_matchup,
            has_batting_order=False,
            data_completeness=sum([has_vegas, has_recent, has_matchup]) / 3,
            matchup_score=dk_projection * np.random.uniform(0.7, 1.3) if has_matchup else 0,
            ownership_proj=5 + true_skill * 20 + (is_ace * 10),
            true_skill=true_skill,
            actual_points=0
        )

    def generate_hitter(self, player_id: int, position: str, game_id: int,
                        team_side: int, batting_order: int, vegas_total: float,
                        team_total: float, weather: float, park_factor: float,
                        is_home: bool) -> MLBPlayer:
        """Generate hitter with realistic attributes"""

        # Position-based salary ranges
        salary_ranges = {
            'C': (2500, 5500),
            '1B': (3000, 6500),
            '2B': (3000, 6000),
            '3B': (3000, 6500),
            'SS': (3000, 6500),
            'OF': (2500, 7000)
        }

        min_sal, max_sal = salary_ranges.get(position, (3000, 6000))

        # Batting order affects everything
        order_mult = (10 - batting_order) / 9

        # Ensure some cheap players
        if np.random.random() < 0.15:  # 15% chance of min salary player
            salary = min_sal
        else:
            # Batting order affects salary
            salary = min_sal + (max_sal - min_sal) * order_mult * 0.8
            salary += np.random.normal(0, 300)
            salary = int(max(min_sal, min(max_sal, salary)))

        salary = round(salary / 100) * 100

        # True skill
        true_skill = 0.6 + order_mult * 0.8 + np.random.normal(0, 0.2)
        true_skill = max(0.3, min(1.8, true_skill))

        # Base projection
        position_base = {'C': 7, '1B': 9, '2B': 8, '3B': 8.5, 'SS': 8, 'OF': 9}
        base = position_base.get(position, 8)
        dk_projection = base * true_skill * (1 + order_mult * 0.2)

        # Data completeness
        has_full_data = np.random.random() < 0.75

        if has_full_data:
            has_vegas = True
            has_recent = True
            has_matchup = True
            has_batting_order = True
        else:
            has_vegas = np.random.random() < 0.8
            has_recent = np.random.random() < 0.85
            has_matchup = np.random.random() < 0.6
            has_batting_order = np.random.random() < 0.9

        # Historical
        recent_games = []
        for i in range(10):
            game_score = dk_projection * np.random.normal(1.0, 0.45)
            game_score = max(0, min(50, game_score))
            recent_games.append(game_score)

        recent_5 = recent_games[:5]
        trend = (np.mean(recent_5) - np.mean(recent_games[5:])) / (np.mean(recent_games) + 1)

        # Platoon advantage
        platoon = np.random.choice([0.85, 1.0, 1.15], p=[0.25, 0.5, 0.25])

        return MLBPlayer(
            id=player_id,
            name=f"{position}{player_id}",
            position=position,
            salary=salary,
            team=f"TM{team_side}",
            opponent=f"TM{1 - team_side}",
            dk_projection=dk_projection,
            base_projection=dk_projection * 0.9,
            vegas_total=vegas_total if has_vegas else 0,
            team_total=team_total if has_vegas else 0,
            spread=np.random.normal(0, 1.5) if has_vegas else 0,
            recent_avg=np.mean(recent_games) if has_recent else 0,
            recent_ceiling=max(recent_games) if has_recent else 0,
            recent_floor=min(recent_games) if has_recent else 0,
            recent_consistency=1 - np.std(recent_games) / (np.mean(recent_games) + 1) if has_recent else 0,
            season_avg=np.mean(recent_games) * 0.95,
            last_10_avg=np.mean(recent_games),
            last_5_avg=np.mean(recent_5) if has_recent else 0,
            batting_order=batting_order if has_batting_order else 0,
            vs_pitcher_type=dk_projection * platoon,
            park_factor=park_factor,
            weather_score=weather,
            is_home=is_home,
            is_pitcher=False,
            k_rate=0,
            whip=0,
            opposing_lineup_strength=0,
            momentum_score=1.0 + trend,
            platoon_advantage=platoon,
            bullpen_quality=np.random.uniform(0.7, 1.3),
            recent_form_trend=trend,
            has_vegas=has_vegas,
            has_recent=has_recent,
            has_matchup=has_matchup,
            has_batting_order=has_batting_order,
            data_completeness=sum([has_vegas, has_recent, has_matchup, has_batting_order]) / 4,
            matchup_score=dk_projection * platoon if has_matchup else 0,
            ownership_proj=3 + order_mult * 15 + np.random.normal(0, 5),
            true_skill=true_skill,
            actual_points=0
        )

    def calculate_all_scores(self, player: MLBPlayer) -> Dict[str, float]:
        """Calculate scores for ALL methods"""
        scores = {}

        # 1. PURE DATA (Original fixed weights)
        score = player.dk_projection * 0.35
        if player.recent_avg > 0:
            score += player.recent_avg * 0.25
        if player.vegas_total > 0:
            score += (player.team_total / 5) * 0.20
        if player.matchup_score > 0:
            score += player.matchup_score * 0.15
        if not player.is_pitcher and player.batting_order > 0:
            score += ((10 - player.batting_order) / 10) * player.dk_projection * 0.05
        scores['pure_data'] = max(0, score)

        # 2. DYNAMIC (Redistributes weights based on available data)
        weights = {
            'base': (player.dk_projection, 0.35),
            'recent': (player.recent_avg, 0.25) if player.recent_avg > 0 else (0, 0),
            'vegas': (player.team_total / 5, 0.20) if player.vegas_total > 0 else (0, 0),
            'matchup': (player.matchup_score, 0.15) if player.matchup_score > 0 else (0, 0),
            'order': (((10 - player.batting_order) / 10) * player.dk_projection, 0.05)
            if not player.is_pitcher and player.batting_order > 0 else (0, 0)
        }

        active_weights = {k: v for k, v in weights.items() if v[1] > 0}
        if active_weights:
            total_weight = sum(w for _, w in active_weights.values())
            score = sum(val * (weight / total_weight) for val, weight in active_weights.values())
        else:
            score = player.dk_projection
        scores['dynamic'] = max(0, score)

        # 3. ENHANCED PURE (Pure + Environmental factors)
        base_score = scores['pure_data']
        env_mult = player.park_factor * 0.7 + player.weather_score * 0.3
        scores['enhanced_pure'] = max(0, base_score * env_mult)

        # 4. DK ONLY
        scores['dk_only'] = player.dk_projection

        # 5. HYBRID SMART (switches based on data completeness)
        if player.data_completeness >= 0.8:
            scores['hybrid_smart'] = scores['pure_data']
        else:
            scores['hybrid_smart'] = scores['dynamic']

        # 6. RECENCY WEIGHTED (from our tests)
        score = 0
        if player.recent_avg > 0:
            score += player.recent_avg * 0.4
            score += player.momentum_score * player.recent_avg * 0.1
        if player.last_10_avg > 0:
            score += player.last_10_avg * 0.3
        score += player.dk_projection * 0.2
        scores['recency_weighted'] = max(0, score)

        # 7. SEASON LONG ADJUSTED
        if player.season_avg > 0:
            score = player.season_avg * 0.4
        else:
            score = player.dk_projection * 0.4
        score += player.dk_projection * 0.3
        if player.matchup_score > 0:
            score += player.matchup_score * 0.2
        if player.recent_avg > 0:
            score += player.recent_avg * 0.1
        scores['season_long'] = max(0, score)

        # 8. BASEBALL OPTIMIZED
        if player.is_pitcher:
            score = player.dk_projection * 0.4
            score += player.recent_avg * 0.3 if player.recent_avg > 0 else 0
            score += (10 - player.vegas_total) * 0.5 * 0.15 if player.vegas_total > 0 else 0
            score += (2 - player.opposing_lineup_strength) * player.dk_projection * 0.1
            score += player.k_rate * 20 * 0.05
        else:
            score = player.dk_projection * 0.25
            score += player.recent_avg * 0.25 if player.recent_avg > 0 else 0
            score += (player.team_total / 5) * 0.20 if player.team_total > 0 else 0
            score += player.vs_pitcher_type * 0.15
            if player.batting_order > 0:
                score += ((10 - player.batting_order) / 10) * player.dk_projection * 0.10
            score *= player.park_factor
        scores['baseball_optimized'] = max(0, score)

        # 9. BAYESIAN (updates beliefs based on evidence)
        prior = player.dk_projection
        evidence = []

        if player.recent_avg > 0:
            evidence.append((player.recent_avg, 0.3 * player.recent_consistency))
        if player.vegas_total > 0:
            evidence.append((player.team_total / 5, 0.25))
        if player.matchup_score > 0:
            evidence.append((player.matchup_score, 0.15))

        if evidence:
            total_evidence_weight = sum(w for _, w in evidence)
            posterior = prior * 0.3
            for value, weight in evidence:
                posterior += value * weight
            score = posterior / (0.3 + total_evidence_weight)
        else:
            score = prior
        scores['bayesian'] = max(0, score)

        # 10. CORRELATION AWARE (for stacking)
        base = player.dk_projection
        if player.team_total > 5:
            base *= 1.15
        if player.batting_order in [1, 2, 3, 4] and not player.is_pitcher:
            base *= 1.1
        scores['correlation_aware'] = max(0, base)

        # 11. WEATHER ADJUSTED
        base = player.dk_projection
        if player.is_pitcher:
            if player.weather_score < 0.9:
                base *= 0.9
        else:
            base *= player.weather_score
        base *= player.park_factor
        scores['weather_adjusted'] = max(0, base)

        # 12. ADVANCED STACK (emphasizes team totals and correlation)
        if player.is_pitcher:
            score = player.dk_projection * (2 - player.vegas_total / 10)
        else:
            score = player.dk_projection
            if player.team_total > 5:
                score *= 1.2
            if player.batting_order <= 5:
                score *= 1.15
        scores['advanced_stack'] = max(0, score)

        return scores

    def simulate_actual_performance(self, player: MLBPlayer) -> float:
        """Simulate realistic MLB performance"""
        base = player.base_projection * player.true_skill

        # Position-specific variance
        if player.is_pitcher:
            variance = np.random.normal(1.0, 0.4)
            # Matchup impact
            base *= (2 - player.opposing_lineup_strength)
            # Weather
            if player.weather_score < 0.9:
                base *= 0.9
        else:
            variance = np.random.normal(1.0, 0.45)
            # Batting order
            if player.batting_order <= 3:
                base *= 1.1
            elif player.batting_order >= 7:
                base *= 0.85
            # Park factor
            base *= player.park_factor
            # Platoon
            base *= player.platoon_advantage
            # Team total correlation
            if player.team_total > 5:
                base *= 1.15
            elif player.team_total < 4:
                base *= 0.85

        score = base * variance

        # Boom/bust games
        if player.is_pitcher:
            if np.random.random() < 0.04:  # Gem
                score *= 2.5
            elif np.random.random() < 0.08:  # Disaster
                score = -5
        else:
            if np.random.random() < 0.06:  # Multi-HR
                score *= 2.2
            elif np.random.random() < 0.12:  # 0-fer
                score *= 0.1

        # Realistic caps
        if player.is_pitcher:
            score = max(-10, min(65, score))
        else:
            position_caps = {'C': 35, '1B': 45, '2B': 40, '3B': 40, 'SS': 40, 'OF': 50}
            cap = position_caps.get(player.position, 40)
            score = max(0, min(cap, score))

        return score

    def build_lineup(self, players: List[MLBPlayer], score_method: str) -> Dict:
        """Build optimal MLB lineup with improved algorithm"""
        # Score and sort players
        for p in players:
            p.optimization_score = p.__dict__[f"{score_method}_score"]
            p.value = p.optimization_score / (p.salary / 1000) if p.salary > 0 else 0

        # Position groups
        by_position = defaultdict(list)
        for p in players:
            by_position[p.position].append(p)

        # Sort each position by value
        for pos in by_position:
            by_position[pos].sort(key=lambda x: x.value, reverse=True)

        # Try multiple lineup building strategies
        best_lineup = None
        best_score = -1

        # Strategy 1: Value-based
        lineup1 = self._build_lineup_value_based(by_position)
        if lineup1 and len(lineup1) == 10:
            score1 = sum(p.optimization_score for p in lineup1)
            if score1 > best_score:
                best_lineup = lineup1
                best_score = score1

        # Strategy 2: Score-based
        lineup2 = self._build_lineup_score_based(by_position)
        if lineup2 and len(lineup2) == 10:
            score2 = sum(p.optimization_score for p in lineup2)
            if score2 > best_score:
                best_lineup = lineup2
                best_score = score2

        # Strategy 3: Balanced
        lineup3 = self._build_lineup_balanced(by_position)
        if lineup3 and len(lineup3) == 10:
            score3 = sum(p.optimization_score for p in lineup3)
            if score3 > best_score:
                best_lineup = lineup3
                best_score = score3

        if best_lineup and len(best_lineup) == 10:
            total_salary = sum(p.salary for p in best_lineup)

            # If under minimum, try to upgrade
            if total_salary < self.min_salary:
                best_lineup = self._upgrade_lineup(best_lineup, by_position)
                total_salary = sum(p.salary for p in best_lineup)

            return {
                'lineup': best_lineup,
                'total_salary': total_salary,
                'total_projection': sum(p.optimization_score for p in best_lineup),
                'total_actual': sum(p.actual_points for p in best_lineup),
                'valid': total_salary >= self.min_salary and total_salary <= self.salary_cap
            }
        else:
            return {'valid': False, 'total_actual': 0}

    def _build_lineup_value_based(self, by_position: Dict) -> List[MLBPlayer]:
        """Build lineup prioritizing value"""
        lineup = []
        used_player_ids = set()
        total_salary = 0

        # Fill positions by best value
        for pos in self.roster_positions:
            best_player = None
            for player in by_position[pos]:
                if player.id not in used_player_ids and total_salary + player.salary <= self.salary_cap - 1000:  # Leave buffer
                    best_player = player
                    break

            if best_player:
                lineup.append(best_player)
                used_player_ids.add(best_player.id)
                total_salary += best_player.salary
            else:
                # If no player fits, find cheapest
                for player in reversed(by_position[pos]):  # Reversed = cheapest first
                    if player.id not in used_player_ids:
                        best_player = player
                        break

                if best_player:
                    lineup.append(best_player)
                    used_player_ids.add(best_player.id)
                    total_salary += best_player.salary

        return lineup if len(lineup) == 10 else None

    def _build_lineup_score_based(self, by_position: Dict) -> List[MLBPlayer]:
        """Build lineup prioritizing raw score"""
        # Sort all players by score
        all_players = []
        for pos_players in by_position.values():
            all_players.extend(pos_players)
        all_players.sort(key=lambda x: x.optimization_score, reverse=True)

        lineup = []
        lineup_ids = set()
        position_counts = defaultdict(int)
        total_salary = 0

        for player in all_players:
            if len(lineup) >= 10:
                break

            # Check position limits
            pos_needed = self.roster_positions.count(player.position)
            if position_counts[player.position] >= pos_needed:
                continue

            if player.id not in lineup_ids and total_salary + player.salary <= self.salary_cap:
                lineup.append(player)
                lineup_ids.add(player.id)
                position_counts[player.position] += 1
                total_salary += player.salary

        # Fill missing positions with cheapest available
        for pos in self.roster_positions:
            while position_counts[pos] < self.roster_positions.count(pos):
                for player in by_position[pos]:
                    if player.id not in lineup_ids and total_salary + player.salary <= self.salary_cap:
                        lineup.append(player)
                        lineup_ids.add(player.id)
                        position_counts[pos] += 1
                        total_salary += player.salary
                        break
                else:
                    break

        return lineup if len(lineup) == 10 else None

    def _build_lineup_balanced(self, by_position: Dict) -> List[MLBPlayer]:
        """Build lineup with balanced approach"""
        lineup = []
        total_salary = 0
        remaining_spots = 10
        remaining_budget = self.salary_cap

        # Calculate average salary per spot
        avg_per_spot = remaining_budget / remaining_spots

        # Fill each position
        position_order = ['P', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

        for i, pos in enumerate(position_order):
            # Adjust budget for remaining spots
            if remaining_spots > 0:
                target_salary = remaining_budget / remaining_spots
            else:
                target_salary = avg_per_spot

            # Find best player near target salary
            best_player = None
            best_diff = float('inf')

            for player in by_position[pos]:
                if player not in lineup:
                    if total_salary + player.salary <= self.salary_cap:
                        salary_diff = abs(player.salary - target_salary)
                        # Prefer players closer to target salary but with good value
                        score_bonus = player.value * 1000  # Weight value
                        adjusted_diff = salary_diff - score_bonus

                        if adjusted_diff < best_diff:
                            best_diff = adjusted_diff
                            best_player = player

            if best_player:
                lineup.append(best_player)
                total_salary += best_player.salary
                remaining_budget = self.salary_cap - total_salary
                remaining_spots -= 1

        return lineup if len(lineup) == 10 else None

    def _upgrade_lineup(self, lineup: List[MLBPlayer], by_position: Dict) -> List[MLBPlayer]:
        """Upgrade lineup to meet minimum salary"""
        current_salary = sum(p.salary for p in lineup)

        while current_salary < self.min_salary:
            # Find cheapest player to replace
            min_player = min(lineup, key=lambda x: x.salary)
            remaining_budget = self.salary_cap - current_salary + min_player.salary

            # Find best upgrade
            best_upgrade = None
            best_score = min_player.optimization_score

            for player in by_position[min_player.position]:
                if (player not in lineup and
                        player.salary > min_player.salary and
                        player.salary <= remaining_budget and
                        player.optimization_score > best_score):
                    best_upgrade = player
                    best_score = player.optimization_score

            if best_upgrade:
                lineup.remove(min_player)
                lineup.append(best_upgrade)
                current_salary = sum(p.salary for p in lineup)
            else:
                break

        return lineup

    def run_comprehensive_test(self, num_simulations: int = 1000):
        """Run the ultimate test"""
        print("🏆 ULTIMATE MLB DFS SCORING TEST")
        print("=" * 70)
        print(f"Testing {len(self.scoring_methods)} methods")
        print(f"Running {num_simulations} simulations")
        print("=" * 70)

        # Results storage
        results = defaultdict(lambda: {
            'scores_by_slate': defaultdict(list),
            'all_scores': [],
            'correlations': [],
            'valid_lineups': 0,
            'salary_efficiency': [],
            'data_impact': defaultdict(list)
        })

        slate_types = ['small', 'medium', 'main', 'large']

        # Run simulations
        for sim in range(num_simulations):
            if sim % 100 == 0:
                print(f"Progress: {sim}/{num_simulations}")
                if sim > 0:
                    # Show interim valid rates
                    interim_rates = []
                    for method in self.scoring_methods[:3]:  # Show top 3
                        rate = results[method]['valid_lineups'] / sim * 100
                        interim_rates.append(f"{method}: {rate:.1f}%")
                    print(f"  Valid rates so far: {', '.join(interim_rates)}")

            # Test each slate size
            slate_type = slate_types[sim % len(slate_types)]

            # Generate players
            players = self.generate_realistic_slate(slate_type)

            # Calculate all scores
            for player in players:
                scores = self.calculate_all_scores(player)
                for method, score in scores.items():
                    setattr(player, f"{method}_score", score)

            # Simulate actual performance
            for player in players:
                player.actual_points = self.simulate_actual_performance(player)

            # Build lineups for each method
            for method in self.scoring_methods:
                lineup_result = self.build_lineup(players, method)

                if lineup_result['valid']:
                    actual = lineup_result['total_actual']
                    results[method]['scores_by_slate'][slate_type].append(actual)
                    results[method]['all_scores'].append(actual)
                    results[method]['valid_lineups'] += 1
                    results[method]['salary_efficiency'].append(
                        actual / (lineup_result['total_salary'] / 1000)
                    )

                    # Track data completeness impact
                    avg_completeness = np.mean([p.data_completeness for p in lineup_result['lineup']])
                    results[method]['data_impact'][round(avg_completeness, 1)].append(actual)

                # Calculate correlation
                method_scores = [getattr(p, f"{method}_score") for p in players]
                actual_scores = [p.actual_points for p in players]

                if np.std(method_scores) > 0 and np.std(actual_scores) > 0:
                    corr = np.corrcoef(method_scores, actual_scores)[0, 1]
                    results[method]['correlations'].append(corr)

        # Analyze and display results
        self.display_ultimate_results(results, num_simulations)

    def display_ultimate_results(self, results: Dict, num_simulations: int):
        """Display comprehensive results"""
        print("\n" + "=" * 70)
        print("🏆 ULTIMATE MLB DFS SCORING RESULTS")
        print("=" * 70)

        # Calculate summary stats
        summary = []

        for method in self.scoring_methods:
            if not results[method]['all_scores']:
                continue

            scores = results[method]['all_scores']

            summary.append({
                'method': method,
                'avg_score': np.mean(scores),
                'std_dev': np.std(scores),
                'sharpe': np.mean(scores) / np.std(scores) if np.std(scores) > 0 else 0,
                'floor_25': np.percentile(scores, 25),
                'median': np.median(scores),
                'ceiling_75': np.percentile(scores, 75),
                'ceiling_90': np.percentile(scores, 90),
                'max': max(scores),
                'valid_rate': results[method]['valid_lineups'] / num_simulations * 100,
                'correlation': np.mean(results[method]['correlations']),
                'efficiency': np.mean(results[method]['salary_efficiency'])
            })

        # Sort by average score
        summary.sort(key=lambda x: x['avg_score'], reverse=True)

        # Display overall rankings
        print("\n📊 OVERALL PERFORMANCE RANKINGS:")
        print("-" * 70)

        # First show valid lineup rates
        print("\n🎯 VALID LINEUP RATES:")
        for s in summary[:5]:
            print(f"   {s['method']}: {s['valid_rate']:.1f}%")

        avg_valid_rate = np.mean([s['valid_rate'] for s in summary])
        print(f"\n   Average Valid Rate: {avg_valid_rate:.1f}%")

        if avg_valid_rate < 80:
            print("   ⚠️  Warning: Low valid rates may affect accuracy!")
        else:
            print("   ✅ Good valid rates - results are reliable")

        print("\n📈 PERFORMANCE METRICS:")
        print("-" * 70)

        for i, s in enumerate(summary[:10], 1):  # Top 10 only
            print(f"\n{i}. {s['method'].upper()}:")
            print(f"   Average: {s['avg_score']:.2f} pts")
            print(f"   Valid Lineups: {s['valid_rate']:.1f}% ({int(s['valid_rate'] * num_simulations / 100)} lineups)")
            print(f"   StdDev: {s['std_dev']:.2f}")
            print(f"   Sharpe: {s['sharpe']:.3f}")
            print(f"   25th/50th/75th: {s['floor_25']:.1f} / {s['median']:.1f} / {s['ceiling_75']:.1f}")
            print(f"   90th %ile: {s['ceiling_90']:.1f}")
            print(f"   Max: {s['max']:.1f}")
            print(f"   Correlation: {s['correlation']:.3f}")

        # Performance by slate size
        print("\n📈 PERFORMANCE BY SLATE SIZE:")
        print("-" * 70)

        for slate in ['small', 'medium', 'main', 'large']:
            print(f"\n{slate.upper()} slates:")
            slate_scores = []

            for method in self.scoring_methods[:5]:  # Top 5
                if results[method]['scores_by_slate'][slate]:
                    avg = np.mean(results[method]['scores_by_slate'][slate])
                    slate_scores.append((method, avg))

            slate_scores.sort(key=lambda x: x[1], reverse=True)
            for method, avg in slate_scores[:3]:
                print(f"   {method}: {avg:.2f}")

        # Data completeness impact
        print("\n📊 DATA COMPLETENESS IMPACT:")
        print("-" * 70)

        for method in ['pure_data', 'dynamic', 'enhanced_pure', 'hybrid_smart']:
            data_impact = results[method]['data_impact']
            if data_impact:
                correlations = []
                for completeness, scores in sorted(data_impact.items()):
                    if len(scores) > 5:
                        correlations.append((completeness, np.mean(scores)))

                if len(correlations) > 2:
                    x = [c[0] for c in correlations]
                    y = [c[1] for c in correlations]
                    corr = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0
                    print(f"{method}: Data-Score Correlation = {corr:.3f}")

        # Contest recommendations
        print("\n" + "=" * 70)
        print("🎯 FINAL MLB DFS RECOMMENDATIONS:")
        print("=" * 70)

        # Cash games (low variance)
        cash_best = min(summary[:5], key=lambda x: x['std_dev'])
        print(f"\n💰 CASH GAMES: {cash_best['method'].upper()}")
        print(f"   StdDev: {cash_best['std_dev']:.2f}")
        print(f"   Sharpe: {cash_best['sharpe']:.3f}")

        # GPPs (high ceiling)
        gpp_best = max(summary[:5], key=lambda x: x['ceiling_90'])
        print(f"\n🎯 GPPs: {gpp_best['method'].upper()}")
        print(f"   90th %ile: {gpp_best['ceiling_90']:.1f}")
        print(f"   Max: {gpp_best['max']:.1f}")

        # Best overall
        print(f"\n🏆 BEST OVERALL: {summary[0]['method'].upper()}")
        print(f"   Average: {summary[0]['avg_score']:.2f}")
        print(f"   {(summary[0]['avg_score'] / summary[-1]['avg_score'] - 1) * 100:.1f}% better than worst")

        # Key insights
        print("\n💡 KEY INSIGHTS:")
        print("-" * 70)

        # Compare key methods
        method_map = {m['method']: m for m in summary}

        if 'pure_data' in method_map and 'dynamic' in method_map:
            pure = method_map['pure_data']['avg_score']
            dynamic = method_map['dynamic']['avg_score']
            print(f"\n1. Pure Data vs Dynamic:")
            print(f"   Pure Data: {pure:.2f}")
            print(f"   Dynamic: {dynamic:.2f}")
            if dynamic > pure:
                print(f"   Dynamic wins by {(dynamic / pure - 1) * 100:.1f}%")
            else:
                print(f"   Pure Data wins by {(pure / dynamic - 1) * 100:.1f}%")

        if 'enhanced_pure' in method_map:
            enhanced = method_map['enhanced_pure']['avg_score']
            print(f"\n2. Environmental factors (Enhanced Pure): {enhanced:.2f}")
            print(f"   {'HELP' if enhanced > pure else 'HURT'} performance")

        print(f"\n3. Top 3 Methods:")
        for i in range(min(3, len(summary))):
            print(f"   {i + 1}. {summary[i]['method']} ({summary[i]['avg_score']:.2f})")

        # Final verdict
        print("\n" + "=" * 70)
        print("🎯 FINAL VERDICT FOR MLB DFS:")
        print("=" * 70)

        winner = summary[0]['method']
        print(f"\nUSE: {winner.upper()}")

        if winner == 'dynamic':
            print("\nImplementation:")
            print("- Redistributes weights when data is missing")
            print("- Handles incomplete player data well")
            print("- Best for real-world scenarios")
        elif winner == 'enhanced_pure':
            print("\nImplementation:")
            print("- Pure data + park factors + weather")
            print("- Environmental factors matter in MLB")
        elif winner == 'pure_data':
            print("\nImplementation:")
            print("- Fixed weights work well")
            print("- Simple and reliable")
            print("- No need for complexity")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ultimate_mlb_scoring_results_{timestamp}.json"

        save_data = {
            'timestamp': timestamp,
            'num_simulations': num_simulations,
            'summary': summary,
            'winner': winner
        }

        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"\n📁 Full results saved to: {filename}")

        # Test validity check
        print("\n" + "=" * 70)
        print("🔍 TEST VALIDITY CHECK:")
        print("=" * 70)

        avg_valid = np.mean([s['valid_rate'] for s in summary])
        print(f"\nAverage Valid Lineup Rate: {avg_valid:.1f}%")

        if avg_valid >= 80:
            print("✅ EXCELLENT: High valid rates, results are highly reliable")
        elif avg_valid >= 60:
            print("✅ GOOD: Acceptable valid rates, results are reliable")
        elif avg_valid >= 40:
            print("⚠️  FAIR: Moderate valid rates, results are somewhat reliable")
        else:
            print("❌ POOR: Low valid rates, results may not be accurate")
            print("   Consider running the test again with different parameters")


def main():
    """Run the ultimate test"""
    tester = UltimateMLBTester()
    tester.run_comprehensive_test(num_simulations=1000)
    print("\n✅ Ultimate MLB scoring test complete!")


if __name__ == "__main__":
    main()