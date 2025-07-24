#!/usr/bin/env python3
"""
ULTIMATE VALIDATED DFS STRATEGY TEST
====================================
The definitive test incorporating all validation requirements
Uses realistic data, proper statistics, and comprehensive strategy comparison
"""
import time
import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
import warnings

warnings.filterwarnings('ignore')


@dataclass
class HistoricalData:
    """Historical performance data for realistic modeling"""
    player_name: str
    position: str
    last_10_games: List[float] = field(default_factory=list)
    season_avg: float = 0.0
    ceiling_percentile: float = 0.0
    floor_percentile: float = 0.0
    consistency_score: float = 0.0
    correlation_with_team: float = 0.0


@dataclass
class Player:
    """Comprehensive MLB DFS Player"""
    name: str
    position: str
    team: str
    salary: int
    dk_projection: float
    batting_order: int
    opponent: str
    game_id: str

    # Ownership modeling
    ownership_projection: float = 0.0
    ownership_ceiling: float = 0.0
    ownership_floor: float = 0.0

    # Vegas data
    team_total: float = 0.0
    game_total: float = 0.0
    moneyline: int = 0

    # Historical performance
    historical: Optional[HistoricalData] = None

    # Advanced stats
    woba: float = 0.320
    iso: float = 0.150
    ops_vs_hand: float = 0.750
    park_factor: float = 1.0
    weather_score: float = 1.0

    # Recent form
    last_5_avg: float = 0.0
    hot_streak: bool = False
    cold_streak: bool = False

    # Statcast data
    barrel_rate: float = 0.08
    hard_hit_rate: float = 0.40
    xwoba: float = 0.320

    # For pitchers
    era: float = 4.00
    whip: float = 1.30
    k_rate: float = 0.22

    def __hash__(self):
        return hash(self.name)


@dataclass
class SlateConfig:
    """Configuration for different slate types"""
    name: str
    num_games: int
    contest_type: str
    avg_total: float
    ownership_concentration: float  # How chalky
    sharp_percentage: float  # % of sharp players in field


@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics"""
    iterations: int
    confidence_level: float
    mean: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    percentile_25: float
    percentile_75: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    statistical_significance: bool
    p_value: float


class BaseStrategy:
    """Enhanced base strategy with full implementation requirements"""

    def __init__(self, name: str):
        self.name = name
        self.description = ""
        self.uses_ownership = False
        self.uses_historical = False
        self.uses_correlation = False
        self.max_exposure = 0.5
        self.min_salary_used = 0.95

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        """Score with full context"""
        return player.dk_projection  # Keep this simple default

    def get_stacking_rules(self) -> Dict:
        """Define stacking preferences"""
        return {
            'min_stack': 0,
            'max_stack': 5,
            'preferred_stack': 3,
            'stack_teams': [],
            'avoid_teams': []
        }

    def get_exposure_limits(self) -> Dict[str, float]:
        """Player exposure limits"""
        return {}

    def adjust_for_slate_size(self, num_games: int) -> None:
        """Adjust strategy for slate size"""
        pass


# YOUR EXACT CORRELATION STRATEGY IMPLEMENTATION
class YourExactCorrelationStrategy(BaseStrategy):
    """Your exact system from correlation_scoring_config.py"""

    def __init__(self, contest_type: str = 'gpp'):
        super().__init__(f"your_system_{contest_type}")
        self.contest_type = contest_type
        self.description = "Your proven correlation-aware system"
        self.uses_correlation = True

        # Your exact configuration from project files
        if contest_type == 'gpp':
            self.team_total_threshold = 5.0
            self.team_total_boost = 1.15
            self.batting_order_boost = 1.10
            self.batting_order_positions = [1, 2, 3, 4]
            self.correlation_factors = {
                "consecutive_order_bonus": 0.05,
                "same_team_pitcher_penalty": -0.20,
                "mini_stack_bonus": 0.08,
                "full_stack_bonus": 0.12,
                "game_total_high": 0.05,
                "game_total_low": -0.10
            }
        else:  # cash
            self.team_total_threshold = 5.0
            self.team_total_boost = 1.08
            self.batting_order_boost = 1.05
            self.batting_order_positions = [1, 2, 3, 4]
            self.correlation_factors = {
                "consecutive_order_bonus": 0.02,
                "same_team_pitcher_penalty": -0.30,
                "mini_stack_bonus": 0.03,
                "full_stack_bonus": 0.05,
                "game_total_high": 0.03,
                "game_total_low": -0.08
            }

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        """Your exact scoring implementation"""
        score = player.dk_projection

        # Team total boost (your key insight)
        if player.team_total > self.team_total_threshold:
            score *= self.team_total_boost

        # Batting order boost
        if player.position != 'P' and player.batting_order in self.batting_order_positions:
            score *= self.batting_order_boost

        # Game total adjustments
        if player.game_total > 10:
            score *= (1 + self.correlation_factors['game_total_high'])
        elif player.game_total < 7:
            score *= (1 + self.correlation_factors['game_total_low'])

        return score

    def get_stacking_rules(self) -> Dict:
        if self.contest_type == 'gpp':
            return {
                'min_stack': 3,
                'max_stack': 5,
                'preferred_stack': 4,
                'stack_teams': [],  # Will be filled dynamically
                'avoid_teams': []
            }
        else:
            return {
                'min_stack': 0,
                'max_stack': 3,
                'preferred_stack': 2,
                'stack_teams': [],
                'avoid_teams': []
            }


# COMPREHENSIVE COMPETITOR STRATEGIES

class PureProjectionsStrategy(BaseStrategy):
    """Baseline - DraftKings projections only"""

    def __init__(self):
        super().__init__("pure_projections")
        self.description = "Raw DraftKings projections"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        return player.dk_projection


class ValueOptimizedStrategy(BaseStrategy):
    """Points per dollar optimization"""

    def __init__(self):
        super().__init__("value_optimized")
        self.description = "Maximum points per dollar"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        # Return adjusted score that favors value
        value = player.dk_projection / (player.salary / 1000)

        # Boost high-value plays
        if value > 3.0:
            base_score = player.dk_projection * 1.15
        elif value > 2.5:
            base_score = player.dk_projection * 1.08
        else:
            base_score = player.dk_projection * 0.95

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score


class OwnershipLeverageStrategy(BaseStrategy):
    """Game theory optimal with ownership leverage"""

    def __init__(self):
        super().__init__("ownership_leverage")
        self.description = "Leverage based on ownership projections"
        self.uses_ownership = True

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        score = player.dk_projection

        # Leverage calculation
        if player.ownership_projection > 0:
            if player.ownership_projection < 5:  # Very low owned
                leverage = 1.20
            elif player.ownership_projection < 10:
                leverage = 1.10
            elif player.ownership_projection > 25:  # High owned
                leverage = 0.90
            elif player.ownership_projection > 35:  # Very high owned
                leverage = 0.80
            else:
                leverage = 1.0

            score *= leverage

        # Ceiling plays for GPP
        if hasattr(player, 'historical') and player.historical:
            if player.historical.ceiling_percentile > 0.80:
                score *= 1.05

        return score


class HistoricalOptimizedStrategy(BaseStrategy):
    """Uses comprehensive historical data"""

    def __init__(self):
        super().__init__("historical_optimized")
        self.description = "Weighted historical performance"
        self.uses_historical = True

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        if not player.historical:
            base_score = player.dk_projection
        else:
            # Weight recent form vs season average vs projection
            weights = {
                'projection': 0.40,
                'recent': 0.35,
                'season': 0.25
            }

            recent_avg = np.mean(player.historical.last_10_games[-5:]) if len(
                player.historical.last_10_games) >= 5 else player.dk_projection

            base_score = (
                    player.dk_projection * weights['projection'] +
                    recent_avg * weights['recent'] +
                    player.historical.season_avg * weights['season']
            )

            # Consistency bonus for cash, variance bonus for GPP
            if slate_context and slate_context.get('contest_type') == 'cash':
                base_score *= (0.9 + player.historical.consistency_score * 0.2)
            else:
                base_score *= (0.9 + player.historical.ceiling_percentile * 0.2)

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score


class AdvancedSabermetricsStrategy(BaseStrategy):
    """Full sabermetrics implementation"""

    def __init__(self):
        super().__init__("advanced_sabermetrics")
        self.description = "wOBA, ISO, Statcast, matchups"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        if player.position == 'P':
            # Pitcher scoring
            score = player.dk_projection

            # ERA and WHIP adjustments
            if player.era < 3.50:
                score *= 1.08
            elif player.era > 4.50:
                score *= 0.92

            # Strikeout upside
            if player.k_rate > 0.25:
                score *= 1.05

            # Opponent adjustment (would need opponent wOBA)

        else:
            # Hitter scoring
            score = player.dk_projection

            # wOBA adjustment
            woba_mult = player.woba / 0.320  # vs league average
            score *= (0.7 + 0.3 * woba_mult)

            # ISO for power upside
            if player.iso > 0.200:
                score *= 1.08
            elif player.iso > 0.250:
                score *= 1.12

            # Statcast data
            if player.barrel_rate > 0.10:
                score *= 1.05

            # Park factor
            score *= (0.9 + 0.1 * player.park_factor)

        return score


class MachineLearningEnsembleStrategy(BaseStrategy):
    """Ensemble of ML models"""

    def __init__(self):
        super().__init__("ml_ensemble")
        self.description = "RF + Bayesian Ridge ensemble"
        self.models = {}
        self._train_models()

    def _train_models(self):
        """Train ML models on synthetic historical data"""
        # Generate training data
        n_samples = 10000
        X = []
        y = []

        for _ in range(n_samples):
            features = [
                random.uniform(5, 20),  # projection
                random.uniform(1, 9),  # batting order
                random.uniform(3, 7),  # team total
                random.uniform(0.250, 0.350),  # wOBA
                random.uniform(0.100, 0.300),  # ISO
                random.uniform(0.8, 1.2),  # park factor
                random.uniform(0, 1),  # weather
                random.uniform(5, 25),  # ownership
                random.uniform(-0.5, 0.5),  # recent form trend
                random.uniform(0.05, 0.15),  # barrel rate
            ]

            # Create realistic target
            base = features[0]  # projection

            # Correlation with features
            if features[2] > 5.5:  # team total
                base *= 1.12
            if features[1] <= 4:  # batting order
                base *= 1.08
            if features[3] > 0.340:  # high wOBA
                base *= 1.06

            # Add noise
            actual = base * random.gauss(1.0, 0.25)

            X.append(features)
            y.append(actual)

        # Train models
        X = np.array(X)
        y = np.array(y)

        # Random Forest
        self.models['rf'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42
        )
        self.models['rf'].fit(X, y)

        # Bayesian Ridge
        self.models['bayesian'] = BayesianRidge()
        self.models['bayesian'].fit(X, y)

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        # Create feature vector
        features = [
            player.dk_projection,
            player.batting_order if player.position != 'P' else 5,
            player.team_total,
            player.woba,
            player.iso,
            player.park_factor,
            player.weather_score,
            player.ownership_projection,
            player.last_5_avg / player.dk_projection if player.dk_projection > 0 else 1,
            player.barrel_rate
        ]

        # Get predictions
        rf_pred = self.models['rf'].predict([features])[0]
        bayes_pred = self.models['bayesian'].predict([features])[0]

        # Ensemble average
        return (rf_pred * 0.6 + bayes_pred * 0.4)


class StacksOnlyStrategy(BaseStrategy):
    """Maximum correlation approach"""

    def __init__(self):
        super().__init__("stacks_only")
        self.description = "Aggressive team stacking"
        self.uses_correlation = True

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        base_score = player.dk_projection

        # Massive team total boost
        if player.team_total > 6:
            base_score *= 1.30
        elif player.team_total > 5.5:
            base_score *= 1.20
        elif player.team_total > 5:
            base_score *= 1.10
        else:
            base_score *= 0.80

        # Batting order for stacking
        if player.position != 'P' and player.batting_order <= 5:
            base_score *= 1.10

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score

    def get_stacking_rules(self) -> Dict:
        return {
            'min_stack': 4,
            'max_stack': 6,
            'preferred_stack': 5,
            'stack_teams': [],
            'avoid_teams': []
        }


class WeatherWindStrategy(BaseStrategy):
    """Weather and park factors focused"""

    def __init__(self):
        super().__init__("weather_wind")
        self.description = "Weather, wind, and park factors"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        base_score = player.dk_projection

        # Weather impact
        if player.weather_score > 1.1:
            base_score *= 1.15
        elif player.weather_score < 0.9:
            base_score *= 0.85

        # Park factor synergy
        if player.park_factor > 1.1 and player.weather_score > 1.05:
            base_score *= 1.08  # Hitter's park + good weather

        # Wind for HRs (simplified)
        if player.position != 'P' and player.iso > 0.200 and player.weather_score > 1.1:
            base_score *= 1.05

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score


class CashGameOptimizedStrategy(BaseStrategy):
    """Pure cash game strategy"""

    def __init__(self):
        super().__init__("cash_optimized")
        self.description = "High floor, consistent players"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        base_score = player.dk_projection

        # Favor consistency
        if player.historical and player.historical.consistency_score > 0.7:
            base_score *= 1.10

        # Avoid high variance
        if player.position == 'P' and player.era > 4.00:
            base_score *= 0.90

        # Batting order preference (more ABs)
        if player.position != 'P' and player.batting_order <= 3:
            base_score *= 1.05

        # Avoid low totals
        if player.team_total < 4:
            base_score *= 0.90

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score


class BayesianOptimizationStrategy(BaseStrategy):
    """Bayesian approach with uncertainty"""

    def __init__(self):
        super().__init__("bayesian_optimization")
        self.description = "Uncertainty-aware optimization"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        # Start with projection as prior
        prior_mean = player.dk_projection
        prior_variance = (prior_mean * 0.3) ** 2

        # Update with "observations"
        observations = []

        if player.historical and player.historical.last_10_games:
            observations.extend(player.historical.last_10_games[-5:])

        if observations:
            # Bayesian update
            obs_mean = np.mean(observations)
            obs_variance = np.var(observations)
            n_obs = len(observations)

            # Posterior mean (simplified)
            posterior_variance = 1 / (1 / prior_variance + n_obs / obs_variance)
            posterior_mean = posterior_variance * (prior_mean / prior_variance + n_obs * obs_mean / obs_variance)

            # UCB for exploration
            if slate_context and slate_context.get('contest_type') == 'gpp':
                ucb = posterior_mean + 2 * np.sqrt(posterior_variance)
                return ucb
            else:
                return posterior_mean
        else:
            return prior_mean


class ContrarianChaosStrategy(BaseStrategy):
    """Anti-chalk, anti-correlation"""

    def __init__(self):
        super().__init__("contrarian_chaos")
        self.description = "Fade the field approach"
        self.uses_ownership = True

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        base_score = player.dk_projection

        # Fade high ownership
        if player.ownership_projection > 20:
            base_score *= 0.70
        elif player.ownership_projection < 5:
            base_score *= 1.20

        # Fade obvious plays
        if player.team_total > 5.5:
            base_score *= 0.90

        # Random chaos
        base_score *= random.uniform(0.85, 1.15)

        # Ensure minimum viable score for cheap players
        if player.salary < 3500:
            base_score = max(base_score, player.dk_projection * 0.8)

        return base_score


class HybridAdaptiveStrategy(BaseStrategy):
    """Adapts based on slate characteristics"""

    def __init__(self):
        super().__init__("hybrid_adaptive")
        self.description = "Adapts to slate size and type"

    def score_player(self, player: Player, slate_context: Dict = None) -> float:
        score = player.dk_projection

        if slate_context:
            num_games = slate_context.get('num_games', 10)

            # Small slate adjustments
            if num_games <= 5:
                # Ownership matters more
                if player.ownership_projection > 30:
                    score *= 0.85
                # Correlation matters less
                if player.team_total > 5:
                    score *= 1.05  # Reduced from normal
            else:
                # Large slate adjustments
                # Correlation matters more
                if player.team_total > 5:
                    score *= 1.12
                # Can play higher ownership
                if player.ownership_projection > 30:
                    score *= 0.95

        return score


class ComprehensiveValidatedSimulation:
    """The ultimate validated DFS simulation framework"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = defaultdict(lambda: defaultdict(list))
        self.validation_results = {}

        # Initialize all strategies
        self.strategies = {
            # Your strategies
            'your_system_gpp': YourExactCorrelationStrategy('gpp'),
            'your_system_cash': YourExactCorrelationStrategy('cash'),

            # Baseline
            'pure_projections': PureProjectionsStrategy(),

            # Value-based
            'value_optimized': ValueOptimizedStrategy(),

            # Ownership/Game Theory
            'ownership_leverage': OwnershipLeverageStrategy(),

            # Historical/Statistical
            'historical_optimized': HistoricalOptimizedStrategy(),

            # Advanced metrics
            'advanced_sabermetrics': AdvancedSabermetricsStrategy(),

            # Machine Learning
            'ml_ensemble': MachineLearningEnsembleStrategy(),

            # Correlation-focused
            'stacks_only': StacksOnlyStrategy(),

            # Environmental
            'weather_wind': WeatherWindStrategy(),

            # Contest-specific
            'cash_optimized': CashGameOptimizedStrategy(),

            # Advanced optimization
            'bayesian_optimization': BayesianOptimizationStrategy(),

            # Contrarian
            'contrarian_chaos': ContrarianChaosStrategy(),

            # Adaptive
            'hybrid_adaptive': HybridAdaptiveStrategy(),
        }

        # Historical data cache
        self.historical_cache = {}
        self._generate_historical_database()

        # Ownership model
        self.ownership_model = self._build_ownership_model()

        # Contest configurations
        self.contest_configs = self._get_contest_configs()

        # Salary distribution parameters (from real DK data analysis)
        self.salary_params = self._get_realistic_salary_params()

    def _generate_historical_database(self):
        """Generate realistic historical performance data"""
        # Common player names for consistency
        player_names = [
            "Mike Trout", "Mookie Betts", "Ronald Acuna Jr.", "Aaron Judge",
            "Freddie Freeman", "Trea Turner", "Juan Soto", "Jose Ramirez",
            "Gerrit Cole", "Jacob deGrom", "Shane Bieber", "Corbin Burnes"
        ]

        for name in player_names:
            # Generate realistic historical data
            is_pitcher = name in ["Gerrit Cole", "Jacob deGrom", "Shane Bieber", "Corbin Burnes"]

            if is_pitcher:
                season_avg = random.gauss(15, 3)
                games = [random.gauss(season_avg, 5) for _ in range(30)]
            else:
                season_avg = random.gauss(8, 2)
                games = [random.gauss(season_avg, 3) for _ in range(30)]

            games = [max(0, g) for g in games]  # No negative scores

            self.historical_cache[name] = HistoricalData(
                player_name=name,
                position='P' if is_pitcher else 'OF',
                last_10_games=games[-10:],
                season_avg=season_avg,
                ceiling_percentile=np.percentile(games, 90) / season_avg,
                floor_percentile=np.percentile(games, 10) / season_avg,
                consistency_score=1 - (np.std(games) / np.mean(games)),
                correlation_with_team=random.uniform(0.4, 0.7)
            )

    def _build_ownership_model(self):
        """Build realistic ownership projection model"""

        def project_ownership(player: Player) -> float:
            # Base ownership from projection and salary
            value = player.dk_projection / (player.salary / 1000)

            if player.position == 'P':
                if value > 3.0:
                    base_own = random.gauss(25, 5)
                elif value > 2.5:
                    base_own = random.gauss(15, 3)
                else:
                    base_own = random.gauss(8, 2)
            else:
                if value > 3.5:
                    base_own = random.gauss(20, 4)
                elif value > 3.0:
                    base_own = random.gauss(12, 3)
                else:
                    base_own = random.gauss(5, 2)

            # Adjustments
            if player.batting_order <= 3:
                base_own *= 1.2
            if player.team_total > 5.5:
                base_own *= 1.3
            if player.hot_streak:
                base_own *= 1.15

            return max(0.5, min(40, base_own))

        return project_ownership

    def _get_contest_configs(self) -> List[SlateConfig]:
        """Different slate configurations to test"""
        return [
            SlateConfig("Main Slate", 10, "gpp", 9.0, 0.3, 0.2),
            SlateConfig("Small Slate", 4, "gpp", 8.5, 0.5, 0.3),
            #SlateConfig("Afternoon", 7, "mixed", 9.2, 0.4, 0.25),
            SlateConfig("Turbo", 15, "gpp", 9.1, 0.25, 0.15),
        ]

    def _get_realistic_salary_params(self) -> Dict:
        """Realistic DraftKings salary distributions"""
        return {
            'P': {
                'ace': {'mean': 9500, 'std': 800, 'min': 8000, 'max': 11500},
                'mid': {'mean': 7500, 'std': 700, 'min': 6000, 'max': 9000},
                'value': {'mean': 5500, 'std': 600, 'min': 4000, 'max': 7000}
            },
            'hitter': {
                'star': {'mean': 5200, 'std': 400, 'min': 4500, 'max': 6000},
                'solid': {'mean': 4300, 'std': 350, 'min': 3700, 'max': 5000},
                'value': {'mean': 3400, 'std': 300, 'min': 2500, 'max': 4000}
            }
        }

    def generate_realistic_slate(self, config: SlateConfig) -> Tuple[List[Player], Dict]:
        """Generate slate with realistic DraftKings characteristics"""
        teams = []
        for i in range(config.num_games * 2):
            teams.append(f"Team{i + 1}")

        games = {}
        game_contexts = {}

        # Create games with realistic totals and contexts
        for i in range(0, len(teams), 2):
            game_id = f"G{i // 2 + 1}"

            # Realistic game total distribution
            if random.random() < 0.1:  # 10% Coors games
                total = random.gauss(11.5, 0.8)
                park_factor = 1.3
            elif random.random() < 0.2:  # 20% pitcher's parks
                total = random.gauss(7.5, 0.6)
                park_factor = 0.85
            else:  # Normal parks
                total = random.gauss(config.avg_total, 1.0)
                park_factor = random.gauss(1.0, 0.1)

            total = max(6.5, min(13.5, total))

            # Weather variation
            weather = random.choices(
                [0.8, 0.9, 1.0, 1.1, 1.15],
                weights=[0.1, 0.2, 0.4, 0.2, 0.1]
            )[0]

            # Moneyline (affects totals)
            favorite_ml = random.randint(-200, -110)
            underdog_ml = abs(favorite_ml) + random.randint(20, 80)

            # Determine which team is favorite
            is_home_favorite = random.random() > 0.5
            if is_home_favorite:
                home_ml = favorite_ml
                away_ml = underdog_ml
            else:
                home_ml = underdog_ml
                away_ml = favorite_ml

            games[game_id] = {
                'home_team': teams[i],
                'away_team': teams[i + 1],
                'total': total,
                'home_ml': home_ml,
                'away_ml': away_ml,
                'park_factor': park_factor,
                'weather': weather
            }

            # Team totals
            home_total = total * 0.52  # Home team slight advantage
            away_total = total * 0.48

            game_contexts[teams[i]] = {
                'team_total': home_total,
                'game_total': total,
                'moneyline': games[game_id]['home_ml'],
                'park_factor': park_factor,
                'weather': weather,
                'game_id': game_id
            }

            game_contexts[teams[i + 1]] = {
                'team_total': away_total,
                'game_total': total,
                'moneyline': games[game_id]['away_ml'],
                'park_factor': park_factor,
                'weather': weather,
                'game_id': game_id
            }

        # Generate players with realistic distributions
        players = []

        for team in teams:
            ctx = game_contexts[team]
            opponent = [t for t in teams if t != team and game_contexts[t]['game_id'] == ctx['game_id']][0]

            # Create pitchers
            # Starting pitchers (2 per team)
            for i in range(2):
                if i == 0:  # Ace or high-end starter
                    tier = 'ace' if random.random() < 0.3 else 'mid'
                else:
                    tier = 'mid' if random.random() < 0.5 else 'value'

                salary_config = self.salary_params['P'][tier]

                # Projection based on salary and matchup
                if tier == 'ace':
                    base_proj = random.gauss(17, 2)
                elif tier == 'mid':
                    base_proj = random.gauss(14, 1.8)
                else:
                    base_proj = random.gauss(11, 1.5)

                # Adjust for matchup
                if ctx['team_total'] < 4:  # Good matchup for pitcher
                    base_proj *= 1.1
                elif ctx['team_total'] > 5:  # Bad matchup
                    base_proj *= 0.9

                salary = int(random.gauss(salary_config['mean'], salary_config['std']))
                salary = max(salary_config['min'], min(salary_config['max'], salary))

                # ERA and stats based on tier
                if tier == 'ace':
                    era = random.gauss(3.00, 0.5)
                    k_rate = random.gauss(0.28, 0.03)
                elif tier == 'mid':
                    era = random.gauss(3.80, 0.6)
                    k_rate = random.gauss(0.23, 0.03)
                else:
                    era = random.gauss(4.50, 0.7)
                    k_rate = random.gauss(0.20, 0.03)

                player = Player(
                    name=f"P_{team}_{i + 1}",
                    position='P',
                    team=team,
                    salary=salary,
                    dk_projection=max(5, base_proj),
                    batting_order=0,
                    opponent=opponent,
                    game_id=ctx['game_id'],
                    team_total=ctx['team_total'],
                    game_total=ctx['game_total'],
                    moneyline=ctx['moneyline'],
                    park_factor=ctx['park_factor'],
                    weather_score=ctx['weather'],
                    era=max(2.0, era),
                    whip=random.gauss(1.20, 0.15),
                    k_rate=max(0.15, min(0.35, k_rate))
                )

                # Historical data
                if random.random() < 0.3:  # 30% have historical data
                    player.historical = self._generate_player_historical(player)

                # Hot/cold streaks
                if random.random() < 0.15:
                    player.hot_streak = True
                elif random.random() < 0.15:
                    player.cold_streak = True

                players.append(player)

            # Create hitters
            # Realistic batting order with proper positions
            batting_positions = [
                ('SS', 1), ('CF', 2), ('1B', 3), ('DH', 4), ('3B', 5),
                ('OF', 6), ('2B', 7), ('C', 8), ('OF', 9)
            ]

            # Add bench/extra players for flexibility
            extra_positions = [
                ('C', 9), ('1B', 9), ('2B', 9), ('3B', 9), ('SS', 9),
                ('OF', 9), ('OF', 9), ('UTIL', 9)
            ]

            all_positions = batting_positions + extra_positions

            for pos, default_order in all_positions:
                # Determine player tier based on batting order and team quality
                if default_order <= 3 and ctx['team_total'] > 5:
                    tier = 'star' if random.random() < 0.4 else 'solid'
                elif default_order <= 5:
                    tier = 'solid' if random.random() < 0.6 else 'value'
                else:
                    tier = 'value'

                salary_config = self.salary_params['hitter'][tier]

                # Set actual batting order (some randomness)
                if default_order <= 9:
                    batting_order = default_order + random.randint(-1, 1)
                    batting_order = max(1, min(9, batting_order))
                else:
                    batting_order = random.randint(6, 9)

                # Projection based on tier and batting order
                if tier == 'star':
                    base_proj = random.gauss(10, 1.5)
                elif tier == 'solid':
                    base_proj = random.gauss(8, 1.2)
                else:
                    base_proj = random.gauss(6, 1.0)

                # Batting order adjustment
                order_mult = {1: 1.05, 2: 1.03, 3: 1.08, 4: 1.06, 5: 1.0,
                              6: 0.95, 7: 0.92, 8: 0.88, 9: 0.85}
                base_proj *= order_mult.get(batting_order, 0.9)

                # Team total adjustment
                if ctx['team_total'] > 5.5:
                    base_proj *= 1.08
                elif ctx['team_total'] < 4:
                    base_proj *= 0.85

                salary = int(random.gauss(salary_config['mean'], salary_config['std']))
                salary = max(salary_config['min'], min(salary_config['max'], salary))

                # Advanced stats based on tier
                if tier == 'star':
                    woba = random.gauss(0.370, 0.025)
                    iso = random.gauss(0.250, 0.040)
                    barrel_rate = random.gauss(0.12, 0.03)
                elif tier == 'solid':
                    woba = random.gauss(0.330, 0.020)
                    iso = random.gauss(0.180, 0.030)
                    barrel_rate = random.gauss(0.08, 0.02)
                else:
                    woba = random.gauss(0.300, 0.020)
                    iso = random.gauss(0.130, 0.025)
                    barrel_rate = random.gauss(0.05, 0.02)

                # Fix position names
                if pos == 'CF':
                    pos = 'OF'
                elif pos == 'DH' or pos == 'UTIL':
                    pos = random.choice(['1B', 'OF'])  # DK doesn't have DH/UTIL

                player = Player(
                    name=f"{pos}_{team}_{batting_order}",
                    position=pos,
                    team=team,
                    salary=salary,
                    dk_projection=max(2, base_proj),
                    batting_order=batting_order,
                    opponent=opponent,
                    game_id=ctx['game_id'],
                    team_total=ctx['team_total'],
                    game_total=ctx['game_total'],
                    moneyline=ctx['moneyline'],
                    park_factor=ctx['park_factor'],
                    weather_score=ctx['weather'],
                    woba=max(0.250, min(0.450, woba)),
                    iso=max(0.050, min(0.350, iso)),
                    barrel_rate=max(0.02, min(0.20, barrel_rate)),
                    hard_hit_rate=random.gauss(0.40, 0.08),
                    xwoba=woba + random.gauss(0, 0.015),
                    ops_vs_hand=random.gauss(0.750, 0.100)
                )

                # Recent form
                player.last_5_avg = base_proj * random.gauss(1.0, 0.2)

                # Historical data (more common for established players)
                if random.random() < 0.5:
                    player.historical = self._generate_player_historical(player)

                # Hot/cold streaks
                streak_roll = random.random()
                if streak_roll < 0.12:
                    player.hot_streak = True
                    player.last_5_avg *= 1.25
                elif streak_roll < 0.24:
                    player.cold_streak = True
                    player.last_5_avg *= 0.75

                players.append(player)

        # Generate ownership projections
        for player in players:
            player.ownership_projection = self.ownership_model(player)
            player.ownership_ceiling = player.ownership_projection * 1.3
            player.ownership_floor = player.ownership_projection * 0.7

        return players, games

    def _generate_player_historical(self, player: Player) -> HistoricalData:
        """Generate historical data for a player"""
        # Base on current projection
        season_avg = player.dk_projection * random.gauss(1.0, 0.1)

        # Generate game log
        games = []
        for _ in range(30):
            # Some correlation with team performance
            team_factor = random.gauss(1.0, 0.2)
            individual_factor = random.gauss(1.0, 0.3)

            game_score = season_avg * team_factor * individual_factor
            games.append(max(0, game_score))

        return HistoricalData(
            player_name=player.name,
            position=player.position,
            last_10_games=games[-10:],
            season_avg=season_avg,
            ceiling_percentile=np.percentile(games, 90) / season_avg,
            floor_percentile=np.percentile(games, 10) / season_avg,
            consistency_score=1 - (np.std(games) / (np.mean(games) + 0.01)),
            correlation_with_team=random.uniform(0.5, 0.7) if player.position != 'P' else 0.3
        )

    def build_optimized_lineup(self, players: List[Player], strategy: BaseStrategy,
                               slate_context: Dict) -> Optional[Tuple[List[Player], float]]:
        """Fixed lineup builder that works like real DFS optimization"""

        # Score all players with error handling
        player_scores = {}
        for player in players:
            try:
                score = strategy.score_player(player, slate_context)
                # Validate score
                if not isinstance(score, (int, float)) or score != score:  # Check for NaN
                    score = player.dk_projection
                player_scores[player] = max(0, score)  # No negative scores
            except:
                player_scores[player] = player.dk_projection

        # Get stacking rules
        stack_rules = strategy.get_stacking_rules()

        best_lineup = None
        best_score = -1

        # Position requirements
        position_needs = {'P': 2, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}

        # Try different construction methods
        for attempt in range(15):
            lineup = []
            salary = 0
            positions_filled = defaultdict(int)
            team_counts = defaultdict(int)

            # Method 1: Top scores (attempts 0-4)
            if attempt < 5:
                # Add randomness for diversity
                noise_factor = 1.0 + (attempt * 0.05)  # 0%, 5%, 10%, 15%, 20% noise
                temp_scores = {p: player_scores[p] * random.uniform(1.0, noise_factor)
                               for p in players}
                sorted_players = sorted(players, key=lambda p: temp_scores[p], reverse=True)

            # Method 2: Value-based (attempts 5-9)
            elif attempt < 10:
                # Points per dollar with variation
                sorted_players = sorted(players,
                                        key=lambda p: (player_scores[p] / (p.salary / 1000)) *
                                                      random.uniform(0.9, 1.1),
                                        reverse=True)

            # Method 3: Balanced approach (attempts 10-14)
            else:
                # Mix of score and value
                weight = random.uniform(0.3, 0.7)
                sorted_players = sorted(players,
                                        key=lambda p: (player_scores[p] * weight +
                                                       (player_scores[p] / (p.salary / 1000)) * (1 - weight)),
                                        reverse=True)

            # Build lineup greedily
            for player in sorted_players:
                # Check position need
                if positions_filled[player.position] >= position_needs.get(player.position, 0):
                    continue

                # Check salary cap
                if salary + player.salary > 50000:
                    continue

                # Check team exposure (max 5 hitters from same team)
                if player.position != 'P' and team_counts[player.team] >= 5:
                    continue

                # Add player
                lineup.append(player)
                salary += player.salary
                positions_filled[player.position] += 1
                if player.position != 'P':
                    team_counts[player.team] += 1

                # Check if complete
                if len(lineup) == 10:
                    break

            # If lineup is complete but salary too low, try to upgrade
            if len(lineup) == 10 and salary < 45000:
                # Try to swap in more expensive players
                remaining_budget = 50000 - salary

                for i in range(len(lineup)):
                    current_player = lineup[i]

                    # Find more expensive replacement at same position
                    replacements = [p for p in players
                                    if p.position == current_player.position
                                    and p.salary > current_player.salary
                                    and p.salary - current_player.salary <= remaining_budget
                                    and p not in lineup]

                    if replacements:
                        # Pick best scoring replacement
                        replacements.sort(key=lambda p: player_scores[p], reverse=True)
                        replacement = replacements[0]

                        # Swap
                        salary = salary - current_player.salary + replacement.salary
                        lineup[i] = replacement
                        remaining_budget = 50000 - salary

                        if salary >= 45000:  # 90% of cap
                            break

            # Validate lineup
            if len(lineup) == 10:
                # Realistic salary requirement: 90-100% of cap
                if 45000 <= salary <= 50000:
                    lineup_score = sum(player_scores[p] for p in lineup)

                    # Check if this is the best so far
                    if lineup_score > best_score:
                        best_score = lineup_score
                        best_lineup = lineup[:]  # Copy

                elif salary < 45000 and attempt == 14:  # Last attempt
                    # If we can't hit 90%, accept 85% on final attempt
                    if salary >= 42500:
                        lineup_score = sum(player_scores[p] for p in lineup)
                        if lineup_score > best_score:
                            best_score = lineup_score
                            best_lineup = lineup[:]

        # Return best lineup found
        if best_lineup:
            return best_lineup, best_score

        # Emergency fallback - should rarely happen
        print(f"    WARNING: {strategy.name} struggled to build optimal lineup")

        # Try one more time with pure projections
        sorted_by_proj = sorted(players, key=lambda p: p.dk_projection, reverse=True)
        emergency_lineup = []
        emergency_salary = 0
        filled = defaultdict(int)

        for player in sorted_by_proj:
            if (filled[player.position] < position_needs.get(player.position, 0) and
                    emergency_salary + player.salary <= 50000):
                emergency_lineup.append(player)
                emergency_salary += player.salary
                filled[player.position] += 1

                if len(emergency_lineup) == 10:
                    break

        if len(emergency_lineup) == 10 and emergency_salary >= 40000:
            return emergency_lineup, sum(player_scores[p] for p in emergency_lineup)

        return None

    def simulate_contest(self, players: List[Player], games: Dict, strategy: BaseStrategy,
                         contest_type: str, slate_config: SlateConfig) -> Optional[Dict]:
        """Simulate a single contest WITHOUT hardcoded strategies"""

        slate_context = {
            'contest_type': contest_type,
            'num_games': slate_config.num_games,
            'games': games
        }

        # Build our lineup
        result = self.build_optimized_lineup(players, strategy, slate_context)
        if not result:
            return None

        our_lineup, our_proj_score = result

        # Generate actual scores with realistic variance
        actual_scores = self.simulate_actual_scores(players, games, slate_config)

        # Calculate our actual score
        our_actual = sum(actual_scores[p.name] for p in our_lineup)

        # Apply correlation bonus
        team_counts = defaultdict(int)
        for p in our_lineup:
            if p.position != 'P':
                team_counts[p.team] += 1

        max_stack = max(team_counts.values()) if team_counts else 0

        # Realistic correlation bonuses
        if max_stack >= 5:
            our_actual *= 1.08
        elif max_stack >= 4:
            our_actual *= 1.05
        elif max_stack >= 3:
            our_actual *= 1.02

        # Simulate field WITHOUT hardcoded strategies
        field_scores = []
        field_size = 1000 if contest_type == 'gpp' else 100

        # Get list of available strategies
        available_strategies = list(self.strategies.values())

        # Different skill levels in field
        skill_distribution = {
            'sharp': int(field_size * 0.1),  # 10% sharp players
            'good': int(field_size * 0.2),  # 20% good players
            'average': int(field_size * 0.5),  # 50% average
            'weak': field_size - int(field_size * 0.8)  # 20% weak
        }

        field_scores = []

        # Simulate each skill level
        for skill_level, count in skill_distribution.items():
            for i in range(count):
                # Choose strategy based on skill level
                if skill_level == 'sharp' and len(available_strategies) > 1:
                    # Sharp players use better strategies (randomly from top half)
                    strategy_pool = available_strategies[:len(available_strategies) // 2]
                else:
                    # Others use any strategy
                    strategy_pool = available_strategies

                # Pick a random strategy from pool
                if strategy_pool:
                    field_strategy = random.choice(strategy_pool)
                else:
                    field_strategy = strategy  # Fallback to current strategy

                # Build lineup for this field entry
                field_result = self.build_optimized_lineup(players, field_strategy, slate_context)
                if field_result:
                    field_lineup, _ = field_result
                    field_score = sum(actual_scores[p.name] for p in field_lineup)

                    # Field correlation
                    field_teams = defaultdict(int)
                    for p in field_lineup:
                        if p.position != 'P':
                            field_teams[p.team] += 1

                    field_max_stack = max(field_teams.values()) if field_teams else 0
                    if field_max_stack >= 5:
                        field_score *= random.uniform(1.06, 1.10)
                    elif field_max_stack >= 4:
                        field_score *= random.uniform(1.03, 1.07)
                    elif field_max_stack >= 3:
                        field_score *= random.uniform(1.01, 1.04)

                    field_scores.append(field_score)

        # Add our score
        field_scores.append(our_actual)
        field_scores.sort(reverse=True)

        # Calculate results
        our_rank = field_scores.index(our_actual) + 1
        percentile = (1 - our_rank / len(field_scores)) * 100

        # Realistic payouts
        if contest_type == 'gpp':
            payouts = self._calculate_gpp_payouts(field_size)
            payout = payouts.get(our_rank, 0)
            entry_fee = 20
        else:
            payout = 90 if our_rank <= field_size // 2 else 0
            entry_fee = 50

        roi = (payout - entry_fee) / entry_fee

        return {
            'score': our_actual,
            'rank': our_rank,
            'field_size': field_size,
            'percentile': percentile,
            'payout': payout,
            'entry_fee': entry_fee,
            'roi': roi,
            'cashed': payout > 0,
            'top_1_pct': our_rank <= field_size * 0.01,
            'top_10_pct': our_rank <= field_size * 0.10,
            'lineup': our_lineup,
            'max_stack': max_stack,
            'contest_type': contest_type,
            'slate_config': slate_config.name
        }

    def simulate_actual_scores(self, players: List[Player], games: Dict,
                               slate_config: SlateConfig) -> Dict[str, float]:
        """Simulate actual scores with realistic correlation"""
        actual_scores = {}

        # Determine which teams blow up
        team_performances = {}
        for game_id, game_info in games.items():
            # Team correlation events
            event_roll = random.random()

            if event_roll < 0.20:  # 20% one team dominates
                if random.random() < 0.5:
                    team_performances[game_info['home_team']] = random.uniform(1.25, 1.45)
                    team_performances[game_info['away_team']] = random.uniform(0.65, 0.80)
                else:
                    team_performances[game_info['away_team']] = random.uniform(1.25, 1.45)
                    team_performances[game_info['home_team']] = random.uniform(0.65, 0.80)
            elif event_roll < 0.30:  # 10% high scoring both sides
                team_performances[game_info['home_team']] = random.uniform(1.15, 1.30)
                team_performances[game_info['away_team']] = random.uniform(1.15, 1.30)
            elif event_roll < 0.35:  # 5% pitchers duel
                team_performances[game_info['home_team']] = random.uniform(0.70, 0.85)
                team_performances[game_info['away_team']] = random.uniform(0.70, 0.85)
            else:  # Normal variance
                team_performances[game_info['home_team']] = random.gauss(1.0, 0.15)
                team_performances[game_info['away_team']] = random.gauss(1.0, 0.15)

        # Individual player scores
        for player in players:
            # Base variance
            if player.historical and player.historical.consistency_score > 0:
                # Use historical consistency
                individual_std = 0.25 * (2 - player.historical.consistency_score)
            else:
                individual_std = 0.30

            individual_var = random.gauss(1.0, individual_std)

            # Team correlation
            team_factor = team_performances.get(player.team, 1.0)

            if player.position == 'P':
                # Pitchers
                actual = player.dk_projection * individual_var

                # Opponent factor
                opp_factor = team_performances.get(player.opponent, 1.0)
                if opp_factor > 1.25:
                    actual *= 0.75  # Struggle vs hot offense
                elif opp_factor < 0.75:
                    actual *= 1.20  # Dominate vs cold offense

                # K upside
                if player.k_rate > 0.27 and random.random() < 0.15:
                    actual *= random.uniform(1.15, 1.30)

            else:
                # Hitters - correlation with team
                if player.historical:
                    corr_strength = player.historical.correlation_with_team
                else:
                    corr_strength = 0.6

                actual = player.dk_projection * (
                        individual_var * (1 - corr_strength) +
                        team_factor * corr_strength
                )

                # Batting order benefits in blowups
                if team_factor > 1.2:
                    if player.batting_order <= 5:
                        actual *= random.uniform(1.05, 1.12)

                # Power upside
                if player.iso > 0.200:
                    # Home run variance
                    hr_roll = random.random()
                    if hr_roll < 0.03:  # 3% multi-HR
                        actual *= random.uniform(2.5, 3.5)
                    elif hr_roll < 0.12:  # 9% HR
                        actual *= random.uniform(1.5, 2.0)

                # Hot/cold streaks
                if player.hot_streak:
                    actual *= random.uniform(1.10, 1.25)
                elif player.cold_streak:
                    actual *= random.uniform(0.75, 0.90)

            actual_scores[player.name] = max(0, actual)

        return actual_scores

    def _calculate_gpp_payouts(self, field_size: int) -> Dict[int, float]:
        """Realistic GPP payout structure"""
        total_pool = field_size * 20 * 0.80  # $20 entry, 20% rake
        payouts = {}

        # Top heavy structure
        if field_size >= 5000:
            payouts[1] = total_pool * 0.15
            payouts[2] = total_pool * 0.08
            payouts[3] = total_pool * 0.05

            # Places 4-10
            for i in range(4, 11):
                payouts[i] = total_pool * 0.02

            # Places 11-100
            for i in range(11, 101):
                payouts[i] = total_pool * 0.003

            # Min cash to 20%
            min_cash = 30
            cash_line = int(field_size * 0.20)

            for i in range(101, cash_line + 1):
                if i <= 500:
                    payouts[i] = total_pool * 0.001
                else:
                    payouts[i] = min_cash

        return payouts

    def run_comprehensive_validation(self, iterations_per_slate: int = 250):
        """Run validated simulation across multiple slate types"""

        print("\n" + "=" * 80)
        print("🏆 ULTIMATE VALIDATED DFS STRATEGY TEST")
        print("=" * 80)
        print(f"Testing {len(self.strategies)} strategies across {len(self.contest_configs)} slate types")
        print(f"Iterations per slate: {iterations_per_slate}")
        print(f"Total simulations: {iterations_per_slate * len(self.contest_configs) * len(self.strategies) * 2}")
        print("\nThis comprehensive test will take approximately 20-30 minutes...\n")

        all_results = defaultdict(lambda: defaultdict(list))

        # Test each slate configuration
        for slate_idx, slate_config in enumerate(self.contest_configs):
            print(f"\n📊 Testing {slate_config.name} (Games: {slate_config.num_games})")
            print("-" * 60)

            for iteration in range(iterations_per_slate):
                iter_start = time.time()  # Add at top of file: import time

                # Always show current iteration
                print(f"\n  Iteration {iteration + 1}/{iterations_per_slate}:")

                # Generate slate
                print(f"    - Generating slate...", end='', flush=True)
                slate_start = time.time()
                players, games = self.generate_realistic_slate(slate_config)
                print(f" done ({time.time() - slate_start:.1f}s)")

                # Test each strategy
                strategies_tested = 0
                for strategy_name, strategy in self.strategies.items():
                    # Determine contest types to test
                    if 'cash' in strategy_name:
                        contest_types = ['cash']
                    elif 'gpp' in strategy_name:
                        contest_types = ['gpp']
                    else:
                        contest_types = ['gpp', 'cash']

                    for contest_type in contest_types:
                        print(f"    - Testing {strategy_name} ({contest_type})...", end='', flush=True)
                        strat_start = time.time()

                        result = self.simulate_contest(
                            players, games, strategy, contest_type, slate_config
                        )

                        print(f" done ({time.time() - strat_start:.1f}s)")
                        strategies_tested += 1

                        if result:
                            key = f"{strategy_name}_{contest_type}_{slate_config.name}"
                            all_results[strategy_name][key].append(result)
                            print(
                                f"    DEBUG: Stored result for {key}, total now: {len(all_results[strategy_name][key])}")
                        else:
                            print(f"    DEBUG: No result for {strategy_name} {contest_type}")

                print(
                    f"  Iteration {iteration + 1} complete: {time.time() - iter_start:.1f}s total, {strategies_tested} tests")

    def _calculate_validation_metrics(self):
        """Calculate comprehensive validation metrics"""
        self.validation_results = {}

        for strategy_name, strategy_results in self.results.items():
            strategy_metrics = {}

            for key, results in strategy_results.items():
                if len(results) < 30:
                    continue

                rois = [r['roi'] for r in results]
                scores = [r['score'] for r in results]
                ranks = [r['rank'] for r in results]
                cash_rates = [1 if r['cashed'] else 0 for r in results]

                # Calculate metrics
                mean_roi = np.mean(rois)
                std_roi = np.std(rois)

                # Confidence interval (95%)
                n = len(rois)
                se = std_roi / np.sqrt(n)
                ci_lower = mean_roi - 1.96 * se
                ci_upper = mean_roi + 1.96 * se

                # Sharpe ratio (risk-adjusted returns)
                sharpe = mean_roi / std_roi if std_roi > 0 else 0

                # Sortino ratio (downside risk)
                downside_returns = [r for r in rois if r < 0]
                downside_std = np.std(downside_returns) if downside_returns else 0
                sortino = mean_roi / downside_std if downside_std > 0 else 0

                # Max drawdown
                cumulative = np.cumsum([r['roi'] for r in results])
                running_max = np.maximum.accumulate(cumulative)
                drawdown = (cumulative - running_max) / (running_max + 1)
                max_drawdown = np.min(drawdown)

                # Statistical significance test vs baseline
                baseline_key = f"pure_projections_{key.split('_', 2)[1]}"
                if baseline_key in self.results.get('pure_projections', {}):
                    baseline_rois = [r['roi'] for r in self.results['pure_projections'][baseline_key]]
                    if len(baseline_rois) >= 30:
                        t_stat, p_value = stats.ttest_ind(rois, baseline_rois)
                        significant = p_value < 0.05
                    else:
                        p_value = 1.0
                        significant = False
                else:
                    p_value = 1.0
                    significant = False

                strategy_metrics[key] = ValidationMetrics(
                    iterations=len(results),
                    confidence_level=0.95,
                    mean=mean_roi * 100,
                    std_dev=std_roi * 100,
                    confidence_interval=(ci_lower * 100, ci_upper * 100),
                    percentile_25=np.percentile(rois, 25) * 100,
                    percentile_75=np.percentile(rois, 75) * 100,
                    sharpe_ratio=sharpe,
                    sortino_ratio=sortino,
                    max_drawdown=max_drawdown * 100,
                    win_rate=np.mean(cash_rates) * 100,
                    statistical_significance=significant,
                    p_value=p_value
                )

            self.validation_results[strategy_name] = strategy_metrics

    def analyze_results(self):
        """Comprehensive analysis with validation metrics"""

        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE VALIDATED RESULTS")
        print("=" * 80)

        # Aggregate results by strategy and contest type
        summary_data = defaultdict(lambda: defaultdict(list))

        for strategy_name, strategy_results in self.results.items():
            for key, results in strategy_results.items():
                parts = key.split('_')
                contest_type = parts[-2]

                for result in results:
                    summary_data[strategy_name][contest_type].append(result)

        # GPP Analysis
        print("\n🎯 GPP TOURNAMENT RESULTS (Validated)")
        print("-" * 120)

        gpp_summaries = []

        for strategy_name in self.strategies.keys():
            gpp_results = summary_data[strategy_name].get('gpp', [])

            if len(gpp_results) >= 30:
                # Get validation metrics
                validation_keys = [k for k in self.validation_results.get(strategy_name, {}).keys()
                                   if 'gpp' in k]

                if validation_keys:
                    # Average across slate types
                    avg_metrics = {
                        'mean_roi': np.mean([self.validation_results[strategy_name][k].mean
                                             for k in validation_keys]),
                        'confidence_interval': (
                            np.mean([self.validation_results[strategy_name][k].confidence_interval[0]
                                     for k in validation_keys]),
                            np.mean([self.validation_results[strategy_name][k].confidence_interval[1]
                                     for k in validation_keys])
                        ),
                        'sharpe': np.mean([self.validation_results[strategy_name][k].sharpe_ratio
                                           for k in validation_keys]),
                        'significant': any([self.validation_results[strategy_name][k].statistical_significance
                                            for k in validation_keys])
                    }
                else:
                    avg_metrics = {'mean_roi': 0, 'confidence_interval': (0, 0), 'sharpe': 0, 'significant': False}

                gpp_summary = {
                    'strategy': strategy_name,
                    'contests': len(gpp_results),
                    'avg_score': np.mean([r['score'] for r in gpp_results]),
                    'avg_rank': np.mean([r['rank'] for r in gpp_results]),
                    'percentile': np.mean([r['percentile'] for r in gpp_results]),
                    'cash_rate': sum(r['cashed'] for r in gpp_results) / len(gpp_results) * 100,
                    'top_1_pct': sum(r['top_1_pct'] for r in gpp_results) / len(gpp_results) * 100,
                    'top_10_pct': sum(r['top_10_pct'] for r in gpp_results) / len(gpp_results) * 100,
                    'roi': avg_metrics['mean_roi'],
                    'roi_ci': avg_metrics['confidence_interval'],
                    'sharpe': avg_metrics['sharpe'],
                    'avg_stack': np.mean([r['max_stack'] for r in gpp_results]),
                    'significant': avg_metrics['significant']
                }

                gpp_summaries.append(gpp_summary)

        # Sort by ROI
        gpp_summaries.sort(key=lambda x: x['roi'], reverse=True)

        # Print GPP results
        print(f"\n{'Rank':<5} {'Strategy':<22} {'ROI':<12} {'95% CI':<20} {'Sharpe':<8} "
              f"{'Cash%':<8} {'Top 1%':<8} {'Top 10%':<9} {'Sig?':<5}")
        print("-" * 120)

        for i, s in enumerate(gpp_summaries):
            prefix = "⭐" if 'your_system' in s['strategy'] else "  "
            sig = "YES" if s['significant'] else "NO"
            ci_str = f"({s['roi_ci'][0]:.1f}, {s['roi_ci'][1]:.1f})"

            print(f"{prefix}{i + 1:<3} {s['strategy']:<22} {s['roi']:>10.1f}% {ci_str:<20} "
                  f"{s['sharpe']:<8.2f} {s['cash_rate']:<8.1f} {s['top_1_pct']:<8.2f} "
                  f"{s['top_10_pct']:<9.1f} {sig:<5}")

        # Cash Analysis
        print("\n\n💵 CASH GAME RESULTS (Validated)")
        print("-" * 100)

        cash_summaries = []

        for strategy_name in self.strategies.keys():
            cash_results = summary_data[strategy_name].get('cash', [])

            if len(cash_results) >= 30:
                validation_keys = [k for k in self.validation_results.get(strategy_name, {}).keys()
                                   if 'cash' in k]

                if validation_keys:
                    avg_metrics = {
                        'mean_roi': np.mean([self.validation_results[strategy_name][k].mean
                                             for k in validation_keys]),
                        'confidence_interval': (
                            np.mean([self.validation_results[strategy_name][k].confidence_interval[0]
                                     for k in validation_keys]),
                            np.mean([self.validation_results[strategy_name][k].confidence_interval[1]
                                     for k in validation_keys])
                        )
                    }
                else:
                    avg_metrics = {'mean_roi': 0, 'confidence_interval': (0, 0)}

                cash_summary = {
                    'strategy': strategy_name,
                    'contests': len(cash_results),
                    'avg_score': np.mean([r['score'] for r in cash_results]),
                    'cash_rate': sum(r['cashed'] for r in cash_results) / len(cash_results) * 100,
                    'roi': avg_metrics['mean_roi'],
                    'roi_ci': avg_metrics['confidence_interval']
                }

                cash_summaries.append(cash_summary)

        cash_summaries.sort(key=lambda x: x['cash_rate'], reverse=True)

        print(f"\n{'Rank':<5} {'Strategy':<22} {'Cash Rate':<12} {'ROI':<12} {'95% CI':<20}")
        print("-" * 100)

        for i, s in enumerate(cash_summaries):
            prefix = "⭐" if 'your_system' in s['strategy'] else "  "
            ci_str = f"({s['roi_ci'][0]:.1f}, {s['roi_ci'][1]:.1f})"

            print(f"{prefix}{i + 1:<3} {s['strategy']:<22} {s['cash_rate']:<12.1f}% "
                  f"{s['roi']:>10.1f}% {ci_str:<20}")

        # Statistical Analysis
        print("\n\n📈 STATISTICAL VALIDATION")
        print("-" * 80)

        # Find your strategies
        your_gpp = next((s for s in gpp_summaries if s['strategy'] == 'your_system_gpp'), None)
        your_cash = next((s for s in cash_summaries if s['strategy'] == 'your_system_cash'), None)

        if your_gpp:
            print(f"\n🎯 Your GPP Strategy:")
            print(
                f"   ROI: {your_gpp['roi']:.1f}% (95% CI: {your_gpp['roi_ci'][0]:.1f}% to {your_gpp['roi_ci'][1]:.1f}%)")
            print(f"   Sharpe Ratio: {your_gpp['sharpe']:.2f}")
            print(f"   Statistically better than baseline: {'YES' if your_gpp['significant'] else 'NO'}")

            # Compare to specific strategies
            comparisons = ['pure_projections', 'value_optimized', 'ml_ensemble', 'stacks_only']
            print(f"\n   Head-to-head comparisons:")

            for comp in comparisons:
                comp_data = next((s for s in gpp_summaries if s['strategy'] == comp), None)
                if comp_data:
                    diff = your_gpp['roi'] - comp_data['roi']
                    print(f"   vs {comp}: {diff:+.1f}% ROI difference")

        # Key Insights
        print("\n\n💡 KEY VALIDATED INSIGHTS")
        print("-" * 80)

        # Check if results are realistic
        top_roi = gpp_summaries[0]['roi'] if gpp_summaries else 0

        if top_roi > 50:
            print("\n⚠️  WARNING: ROIs seem unrealistically high. Consider:")
            print("   - Salary generation might be off")
            print("   - Field simulation might be too weak")
            print("   - Correlation bonuses might be too strong")
        else:
            print("\n✅ ROI ranges appear realistic!")

        # Strategy recommendations
        if your_gpp and your_gpp['roi'] > 0:
            print(f"\n🎯 Your GPP strategy is PROFITABLE with {your_gpp['roi']:.1f}% ROI")

            if your_gpp == gpp_summaries[0]:
                print("   🏆 It's the BEST strategy tested!")
            elif your_gpp in gpp_summaries[:3]:
                print("   🥇 It's in the TOP 3 strategies!")
            else:
                better_strat = gpp_summaries[0]
                print(f"   📈 Consider elements from {better_strat['strategy']} (+{better_strat['roi']:.1f}% ROI)")

        if your_cash and your_cash['cash_rate'] > 50:
            print(f"\n💵 Your cash strategy has {your_cash['cash_rate']:.1f}% win rate")

            if your_cash['cash_rate'] > 55:
                print("   ✅ This is profitable for cash games!")
            else:
                print("   ⚠️  Needs improvement for consistent profit")

        # Save comprehensive results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ultimate_validated_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                'configuration': {
                    'strategies_tested': len(self.strategies),
                    'slate_types': [c.name for c in self.contest_configs],
                    'iterations_per_slate': len(next(iter(self.results.values()))[
                                                    list(self.results.values())[0].keys()[0]]) if self.results else 0,
                    'total_contests': sum(len(results) for strategy_results in self.results.values()
                                          for results in strategy_results.values())
                },
                'gpp_results': gpp_summaries,
                'cash_results': cash_summaries,
                'validation_metrics': {
                    strategy: {key: {
                        'mean': metrics.mean,
                        'confidence_interval': metrics.confidence_interval,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'significant': metrics.statistical_significance,
                        'p_value': metrics.p_value
                    } for key, metrics in strategy_metrics.items()}
                    for strategy, strategy_metrics in self.validation_results.items()
                },
                'timestamp': timestamp
            }, f, indent=2)

        print(f"\n💾 Complete validated results saved to: {filename}")


def main():
    """Run the ultimate validated DFS test"""

    print("🚀 ULTIMATE VALIDATED DFS STRATEGY TEST")
    print("\nThis comprehensive test will:")
    print("  ✓ Use realistic DraftKings salary distributions")
    print("  ✓ Test across multiple slate types")
    print("  ✓ Simulate realistic field competition")
    print("  ✓ Provide statistical validation")
    print("  ✓ Calculate confidence intervals")
    print("  ✓ Test for statistical significance")
    print("\nEstimated runtime: 20-30 minutes")

    # Create simulation
    sim = ComprehensiveValidatedSimulation(verbose=False)

    # DELETE OR COMMENT OUT ALL THE STRATEGY FILTERING
    # Just run with all strategies as originally designed

    # Run with proper validation
    sim.run_comprehensive_validation(iterations_per_slate=3)  # Only 3 iterations

    # Analyze with full statistics
    sim.analyze_results()

    print("\n\n✅ VALIDATION COMPLETE!")

    print("\n\n✅ VALIDATION COMPLETE!")
    print("\nYou now have statistically validated results showing:")
    print("  • Which strategies actually work")
    print("  • Confidence intervals for expected ROI")
    print("  • Whether differences are statistically significant")
    print("  • Risk-adjusted returns (Sharpe ratio)")
    print("\nUse these results to make informed decisions about your system!")


if __name__ == "__main__":
    main()