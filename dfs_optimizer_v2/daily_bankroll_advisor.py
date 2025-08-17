#!/usr/bin/env python3
"""
DAILY BANKROLL ADVISOR
======================
Comprehensive daily DFS recommendations:
- What contests to enter
- How much to wager total
- Cash vs GPP allocation
- Maximum entries per contest
- Daily bankroll limits
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from bankroll_manager import BankrollManager, RiskLevel, ContestInfo

logger = logging.getLogger(__name__)


@dataclass
class DailyRecommendation:
    """Complete daily DFS recommendation"""
    total_daily_stake: float
    cash_allocation: float
    gpp_allocation: float
    recommended_contests: List[Dict]
    bankroll_percentage: float
    expected_daily_profit: float
    risk_assessment: str
    max_entries_per_contest: Dict[str, int]


class DailyBankrollAdvisor:
    """Provides comprehensive daily DFS bankroll recommendations"""
    
    def __init__(self, bankroll_manager: BankrollManager):
        self.bankroll_manager = bankroll_manager
        
        # Daily limits based on risk level
        self.daily_limits = {
            RiskLevel.CONSERVATIVE: 0.10,  # 10% of bankroll per day max
            RiskLevel.MODERATE: 0.20,      # 20% of bankroll per day max
            RiskLevel.AGGRESSIVE: 0.25     # 25% of bankroll per day max (scaling approach)
        }
        
        # Cash vs GPP allocation based on risk level
        self.allocation_strategy = {
            RiskLevel.CONSERVATIVE: {'cash': 0.80, 'gpp': 0.20},  # 80% cash, 20% GPP
            RiskLevel.MODERATE: {'cash': 0.65, 'gpp': 0.35},     # 65% cash, 35% GPP
            RiskLevel.AGGRESSIVE: {'cash': 0.75, 'gpp': 0.25}    # 75% cash, 25% GPP (scaling focus)
        }
    
    def get_daily_recommendation(self, available_contests: List[ContestInfo], 
                               slate_size: str = 'medium') -> DailyRecommendation:
        """
        Get comprehensive daily recommendation
        
        Args:
            available_contests: All contests available for the day
            slate_size: Size of the main slate ('small', 'medium', 'large')
        """
        
        # Calculate daily limits
        daily_limit = self.bankroll_manager.current_bankroll * self.daily_limits[self.bankroll_manager.risk_level]
        
        # Get allocation strategy
        allocation = self.allocation_strategy[self.bankroll_manager.risk_level]
        cash_budget = daily_limit * allocation['cash']
        gpp_budget = daily_limit * allocation['gpp']
        
        # Analyze all contests
        cash_contests = [c for c in available_contests if c.contest_type == 'cash']
        gpp_contests = [c for c in available_contests if c.contest_type == 'gpp']
        
        # Get optimal strategy for slate size
        optimal_cash_strategy = self._get_optimal_strategy('cash', slate_size)
        optimal_gpp_strategy = self._get_optimal_strategy('gpp', slate_size)
        
        # Analyze cash opportunities
        cash_recommendations = self._analyze_contest_group(
            cash_contests, optimal_cash_strategy, cash_budget
        )
        
        # Analyze GPP opportunities
        gpp_recommendations = self._analyze_contest_group(
            gpp_contests, optimal_gpp_strategy, gpp_budget
        )
        
        # Combine recommendations
        all_recommendations = cash_recommendations + gpp_recommendations
        
        # Sort by expected profit
        all_recommendations.sort(key=lambda x: x['expected_profit'], reverse=True)
        
        # Calculate totals
        total_stake = sum(r['recommended_stake'] for r in all_recommendations)
        total_expected_profit = sum(r['expected_profit'] for r in all_recommendations)
        
        # Risk assessment
        risk_assessment = self._assess_daily_risk(total_stake, daily_limit)
        
        # Max entries per contest type
        max_entries = self._calculate_max_entries(available_contests)
        
        return DailyRecommendation(
            total_daily_stake=total_stake,
            cash_allocation=sum(r['recommended_stake'] for r in cash_recommendations),
            gpp_allocation=sum(r['recommended_stake'] for r in gpp_recommendations),
            recommended_contests=all_recommendations,
            bankroll_percentage=(total_stake / self.bankroll_manager.current_bankroll) * 100,
            expected_daily_profit=total_expected_profit,
            risk_assessment=risk_assessment,
            max_entries_per_contest=max_entries
        )
    
    def _get_optimal_strategy(self, contest_type: str, slate_size: str) -> str:
        """Get optimal strategy for contest type and slate size"""
        
        strategy_map = {
            'cash': {
                'small': 'optimized_correlation_value',
                'medium': 'optimized_pitcher_dominance', 
                'large': 'optimized_tournament_winner_gpp'
            },
            'gpp': {
                'small': 'projection_monster',
                'medium': 'tournament_winner_gpp',
                'large': 'correlation_value'
            }
        }
        
        return strategy_map.get(contest_type, {}).get(slate_size, 'optimized_pitcher_dominance')
    
    def _analyze_contest_group(self, contests: List[ContestInfo], strategy: str, 
                              budget: float) -> List[Dict]:
        """Analyze a group of contests (cash or GPP)"""
        
        recommendations = []
        remaining_budget = budget
        
        for contest in contests:
            if remaining_budget <= contest.entry_fee:
                continue
            
            # Get stake recommendation
            stake_info = self.bankroll_manager.get_optimal_stake(contest, strategy)
            
            # Adjust for remaining budget
            max_affordable_entries = int(remaining_budget / contest.entry_fee)
            recommended_entries = min(stake_info['recommended_entries'], max_affordable_entries)
            
            if recommended_entries > 0:
                actual_stake = recommended_entries * contest.entry_fee
                expected_profit = actual_stake * (stake_info['avg_roi'] / 100)
                
                recommendations.append({
                    'contest_name': contest.name,
                    'contest_type': contest.contest_type,
                    'entry_fee': contest.entry_fee,
                    'recommended_entries': recommended_entries,
                    'recommended_stake': actual_stake,
                    'expected_profit': expected_profit,
                    'win_rate': stake_info['win_rate'],
                    'avg_roi': stake_info['avg_roi'],
                    'strategy': strategy,
                    'priority': expected_profit / actual_stake if actual_stake > 0 else 0  # ROI ratio
                })
                
                remaining_budget -= actual_stake
        
        # Sort by priority (ROI ratio)
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations
    
    def _assess_daily_risk(self, total_stake: float, daily_limit: float) -> str:
        """Assess the risk level of daily recommendations"""
        
        utilization = total_stake / daily_limit if daily_limit > 0 else 0
        
        if utilization <= 0.5:
            return "LOW RISK - Conservative approach"
        elif utilization <= 0.8:
            return "MODERATE RISK - Balanced approach"
        elif utilization <= 1.0:
            return "HIGH RISK - Aggressive approach"
        else:
            return "EXCESSIVE RISK - Reduce stakes"
    
    def _calculate_max_entries(self, contests: List[ContestInfo]) -> Dict[str, int]:
        """Calculate maximum entries per contest type"""
        
        daily_limit = self.bankroll_manager.current_bankroll * self.daily_limits[self.bankroll_manager.risk_level]
        
        max_entries = {}
        
        for contest in contests:
            # Never more than 20% of daily limit in one contest
            max_single_contest = daily_limit * 0.20
            max_entries[contest.name] = min(
                contest.max_entries,
                int(max_single_contest / contest.entry_fee)
            )
        
        return max_entries
    
    def format_daily_recommendation(self, recommendation: DailyRecommendation) -> str:
        """Format recommendation as readable text"""
        
        text = f"""
🏦 DAILY BANKROLL RECOMMENDATION
{'=' * 50}

💰 DAILY ALLOCATION:
   Total Daily Stake: ${recommendation.total_daily_stake:.2f}
   Cash Allocation: ${recommendation.cash_allocation:.2f}
   GPP Allocation: ${recommendation.gpp_allocation:.2f}
   Bankroll Usage: {recommendation.bankroll_percentage:.1f}%
   
📈 EXPECTED PERFORMANCE:
   Expected Daily Profit: ${recommendation.expected_daily_profit:.2f}
   Risk Assessment: {recommendation.risk_assessment}

🎯 RECOMMENDED CONTESTS:
"""
        
        for i, contest in enumerate(recommendation.recommended_contests[:10], 1):
            text += f"""
   {i}. {contest['contest_name']} ({contest['contest_type'].upper()})
      Entry Fee: ${contest['entry_fee']:.2f}
      Recommended Entries: {contest['recommended_entries']}
      Total Stake: ${contest['recommended_stake']:.2f}
      Expected Profit: ${contest['expected_profit']:.2f}
      Win Rate: {contest['win_rate']:.1f}%
      Strategy: {contest['strategy']}
"""
        
        text += f"""
⚠️ MAXIMUM ENTRIES PER CONTEST:
"""
        
        for contest_name, max_entries in list(recommendation.max_entries_per_contest.items())[:5]:
            text += f"   {contest_name}: {max_entries} max entries\n"
        
        return text


# Sample contests for testing
SAMPLE_DAILY_CONTESTS = [
    # Cash games
    ContestInfo("$1 Double Up", 1.0, 1, 100, 200, "cash", "small"),
    ContestInfo("$3 Double Up", 3.0, 1, 200, 600, "cash", "small"),
    ContestInfo("$5 50/50", 5.0, 1, 500, 2500, "cash", "medium"),
    ContestInfo("$10 Head-to-Head", 10.0, 1, 2, 20, "cash", "small"),
    ContestInfo("$25 50/50", 25.0, 1, 200, 5000, "cash", "large"),
    
    # GPP tournaments
    ContestInfo("$0.25 GPP", 0.25, 20, 50000, 10000, "gpp", "large"),
    ContestInfo("$1 GPP", 1.0, 20, 20000, 15000, "gpp", "large"),
    ContestInfo("$3 GPP", 3.0, 10, 10000, 25000, "gpp", "medium"),
    ContestInfo("$5 Tournament", 5.0, 5, 5000, 20000, "gpp", "medium"),
    ContestInfo("$25 Tournament", 25.0, 3, 2000, 40000, "gpp", "large"),
]


if __name__ == "__main__":
    print("🏦 DAILY BANKROLL ADVISOR TEST")
    print("=" * 60)
    
    # Test with sample data
    from bankroll_manager import BankrollManager, RiskLevel
    
    manager = BankrollManager(1000.0, RiskLevel.MODERATE)
    advisor = DailyBankrollAdvisor(manager)
    
    # Get daily recommendation
    recommendation = advisor.get_daily_recommendation(SAMPLE_DAILY_CONTESTS, 'medium')
    
    # Print formatted recommendation
    print(advisor.format_daily_recommendation(recommendation))
    
    print("\n✅ Daily Bankroll Advisor ready for integration!")
