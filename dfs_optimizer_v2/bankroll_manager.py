#!/usr/bin/env python3
"""
BANKROLL MANAGEMENT SYSTEM
===========================
Optimal stake sizing and contest selection based on bankroll and expected ROI
Implements Kelly Criterion and risk management for DFS
"""

import math
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class ContestInfo:
    """Information about a DFS contest"""
    name: str
    entry_fee: float
    max_entries: int
    total_entries: int
    prize_pool: float
    contest_type: str  # 'cash', 'gpp', 'satellite'
    slate_size: str    # 'small', 'medium', 'large'


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    win_rate: float           # Win rate (0.0 to 1.0)
    avg_roi: float           # Average ROI (as decimal, e.g., 0.85 = 85%)
    std_deviation: float     # Standard deviation of returns
    sample_size: int         # Number of contests in sample


class BankrollManager:
    """Manages bankroll and provides optimal stake sizing recommendations"""
    
    def __init__(self, initial_bankroll: float, risk_level: RiskLevel = RiskLevel.MODERATE):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.risk_level = risk_level
        
        # Risk multipliers for Kelly Criterion
        self.risk_multipliers = {
            RiskLevel.CONSERVATIVE: 0.25,  # 25% of Kelly
            RiskLevel.MODERATE: 0.50,      # 50% of Kelly
            RiskLevel.AGGRESSIVE: 0.75     # 75% of Kelly
        }
        
        # Strategy performance data (from your testing)
        self.strategy_performance = {
            'optimized_correlation_value': StrategyPerformance(
                win_rate=0.574, avg_roi=14.77, std_deviation=2.5, sample_size=176
            ),
            'optimized_pitcher_dominance': StrategyPerformance(
                win_rate=0.565, avg_roi=12.90, std_deviation=2.3, sample_size=186
            ),
            'optimized_tournament_winner_gpp': StrategyPerformance(
                win_rate=0.593, avg_roi=18.52, std_deviation=3.1, sample_size=189
            ),
            'projection_monster': StrategyPerformance(
                win_rate=0.450, avg_roi=116.94, std_deviation=15.2, sample_size=100
            ),
            'tournament_winner_gpp': StrategyPerformance(
                win_rate=0.425, avg_roi=90.14, std_deviation=12.8, sample_size=100
            )
        }
    
    def update_bankroll(self, new_bankroll: float):
        """Update current bankroll"""
        self.current_bankroll = new_bankroll
        logger.info(f"Bankroll updated to ${new_bankroll:,.2f}")
    
    def calculate_kelly_fraction(self, win_rate: float, avg_return: float, 
                                loss_rate: float = None) -> float:
        """
        Calculate Kelly Criterion fraction
        
        Kelly = (bp - q) / b
        where:
        b = odds received (avg_return when winning)
        p = probability of winning
        q = probability of losing (1 - p)
        """
        
        if loss_rate is None:
            loss_rate = 1.0 - win_rate
        
        if avg_return <= 0 or win_rate <= 0:
            return 0.0
        
        # Kelly fraction
        kelly = (win_rate * avg_return - loss_rate) / avg_return
        
        # Never bet more than 25% of bankroll (safety cap)
        return min(kelly, 0.25)
    
    def get_optimal_stake(self, contest: ContestInfo, strategy_name: str) -> Dict:
        """Get optimal stake size for a contest"""
        
        if strategy_name not in self.strategy_performance:
            logger.warning(f"No performance data for strategy: {strategy_name}")
            return self._conservative_stake(contest)
        
        perf = self.strategy_performance[strategy_name]
        
        # Calculate Kelly fraction
        kelly_fraction = self.calculate_kelly_fraction(
            perf.win_rate, perf.avg_roi / 100
        )
        
        # Apply risk multiplier
        risk_multiplier = self.risk_multipliers[self.risk_level]
        adjusted_fraction = kelly_fraction * risk_multiplier
        
        # Calculate recommended stake
        recommended_stake = self.current_bankroll * adjusted_fraction
        
        # Ensure we can afford the entry fee
        max_entries = min(
            contest.max_entries,
            int(self.current_bankroll * 0.20 / contest.entry_fee)  # Never more than 20% of bankroll
        )
        
        recommended_entries = min(
            max_entries,
            max(1, int(recommended_stake / contest.entry_fee))
        )
        
        actual_stake = recommended_entries * contest.entry_fee
        
        # Calculate expected value
        expected_return = actual_stake * (1 + perf.avg_roi / 100)
        expected_profit = expected_return - actual_stake
        
        return {
            'strategy': strategy_name,
            'contest': contest.name,
            'kelly_fraction': kelly_fraction,
            'adjusted_fraction': adjusted_fraction,
            'recommended_stake': recommended_stake,
            'recommended_entries': recommended_entries,
            'actual_stake': actual_stake,
            'expected_return': expected_return,
            'expected_profit': expected_profit,
            'bankroll_percentage': (actual_stake / self.current_bankroll) * 100,
            'risk_level': self.risk_level.value,
            'win_rate': perf.win_rate,
            'avg_roi': perf.avg_roi
        }
    
    def _conservative_stake(self, contest: ContestInfo) -> Dict:
        """Conservative stake for unknown strategies"""
        
        # Conservative: 1-2% of bankroll
        conservative_stake = self.current_bankroll * 0.015
        entries = max(1, int(conservative_stake / contest.entry_fee))
        actual_stake = entries * contest.entry_fee
        
        return {
            'strategy': 'unknown',
            'contest': contest.name,
            'kelly_fraction': 0.015,
            'adjusted_fraction': 0.015,
            'recommended_stake': conservative_stake,
            'recommended_entries': entries,
            'actual_stake': actual_stake,
            'expected_return': actual_stake * 1.05,  # Assume 5% return
            'expected_profit': actual_stake * 0.05,
            'bankroll_percentage': (actual_stake / self.current_bankroll) * 100,
            'risk_level': 'conservative_unknown',
            'win_rate': 0.50,
            'avg_roi': 5.0
        }
    
    def analyze_slate_opportunities(self, contests: List[ContestInfo], 
                                  strategy_name: str) -> List[Dict]:
        """Analyze all contests on a slate and recommend best opportunities"""
        
        opportunities = []
        
        for contest in contests:
            stake_info = self.get_optimal_stake(contest, strategy_name)
            
            # Add contest-specific metrics
            stake_info.update({
                'entry_fee': contest.entry_fee,
                'max_entries': contest.max_entries,
                'contest_type': contest.contest_type,
                'slate_size': contest.slate_size,
                'field_size': contest.total_entries,
                'overlay': max(0, contest.prize_pool - (contest.total_entries * contest.entry_fee))
            })
            
            opportunities.append(stake_info)
        
        # Sort by expected profit (descending)
        opportunities.sort(key=lambda x: x['expected_profit'], reverse=True)
        
        return opportunities
    
    def get_bankroll_summary(self) -> Dict:
        """Get current bankroll status and recommendations"""
        
        growth_rate = ((self.current_bankroll - self.initial_bankroll) / self.initial_bankroll) * 100
        
        # Risk assessment
        if self.current_bankroll < self.initial_bankroll * 0.5:
            risk_status = "HIGH RISK - Consider reducing stakes"
        elif self.current_bankroll < self.initial_bankroll * 0.8:
            risk_status = "MODERATE RISK - Play conservatively"
        elif self.current_bankroll > self.initial_bankroll * 1.5:
            risk_status = "EXCELLENT - Consider increasing stakes"
        else:
            risk_status = "GOOD - Continue current approach"
        
        return {
            'initial_bankroll': self.initial_bankroll,
            'current_bankroll': self.current_bankroll,
            'growth_amount': self.current_bankroll - self.initial_bankroll,
            'growth_rate': growth_rate,
            'risk_level': self.risk_level.value,
            'risk_status': risk_status,
            'max_single_stake': self.current_bankroll * 0.05,  # 5% max
            'recommended_daily_limit': self.current_bankroll * 0.20  # 20% daily max
        }
    
    def simulate_bankroll_growth(self, daily_stakes: List[float], 
                               strategy_name: str, days: int = 30) -> Dict:
        """Simulate bankroll growth over time"""
        
        if strategy_name not in self.strategy_performance:
            return {'error': f'No performance data for {strategy_name}'}
        
        perf = self.strategy_performance[strategy_name]
        bankroll = self.current_bankroll
        daily_results = []
        
        for day in range(days):
            daily_stake = daily_stakes[day % len(daily_stakes)]
            
            # Simulate result based on strategy performance
            import random
            if random.random() < perf.win_rate:
                # Win
                return_amount = daily_stake * (1 + perf.avg_roi / 100)
                profit = return_amount - daily_stake
            else:
                # Loss
                return_amount = 0
                profit = -daily_stake
            
            bankroll += profit
            daily_results.append({
                'day': day + 1,
                'stake': daily_stake,
                'return': return_amount,
                'profit': profit,
                'bankroll': bankroll
            })
        
        final_growth = ((bankroll - self.current_bankroll) / self.current_bankroll) * 100
        
        return {
            'initial_bankroll': self.current_bankroll,
            'final_bankroll': bankroll,
            'total_profit': bankroll - self.current_bankroll,
            'growth_rate': final_growth,
            'daily_results': daily_results,
            'strategy': strategy_name,
            'simulation_days': days
        }


# Example contest data
SAMPLE_CONTESTS = [
    ContestInfo("$3 Double Up", 3.0, 1, 100, 300, "cash", "small"),
    ContestInfo("$5 50/50", 5.0, 1, 200, 1000, "cash", "medium"),
    ContestInfo("$10 Head-to-Head", 10.0, 1, 2, 20, "cash", "small"),
    ContestInfo("$1 GPP", 1.0, 20, 10000, 8000, "gpp", "large"),
    ContestInfo("$5 GPP", 5.0, 10, 5000, 20000, "gpp", "medium"),
    ContestInfo("$25 Tournament", 25.0, 3, 1000, 20000, "gpp", "large"),
]


if __name__ == "__main__":
    print("🏦 BANKROLL MANAGEMENT SYSTEM TEST")
    print("=" * 60)
    
    # Test bankroll manager
    manager = BankrollManager(1000.0, RiskLevel.MODERATE)
    
    print(f"Initial bankroll: ${manager.current_bankroll:,.2f}")
    print(f"Risk level: {manager.risk_level.value}")
    
    # Test stake calculation
    contest = SAMPLE_CONTESTS[0]  # $3 Double Up
    stake_info = manager.get_optimal_stake(contest, 'optimized_correlation_value')
    
    print(f"\nStake recommendation for {contest.name}:")
    print(f"  Recommended entries: {stake_info['recommended_entries']}")
    print(f"  Total stake: ${stake_info['actual_stake']:.2f}")
    print(f"  Expected profit: ${stake_info['expected_profit']:.2f}")
    print(f"  Bankroll %: {stake_info['bankroll_percentage']:.1f}%")
    
    # Test slate analysis
    opportunities = manager.analyze_slate_opportunities(SAMPLE_CONTESTS, 'optimized_correlation_value')
    
    print(f"\nTop 3 opportunities:")
    for i, opp in enumerate(opportunities[:3]):
        print(f"  {i+1}. {opp['contest']}: ${opp['expected_profit']:.2f} profit")
    
    print("\n✅ Bankroll management system ready!")
