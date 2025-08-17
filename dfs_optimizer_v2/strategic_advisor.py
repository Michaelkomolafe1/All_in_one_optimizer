#!/usr/bin/env python3
"""
STRATEGIC ADVISOR
=================
Enhanced DFS strategy recommendations including:
- Slate size optimization (small/medium/large)
- Contest size recommendations (field size strategy)
- Advanced strategic guidance
- Market timing recommendations
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from daily_bankroll_advisor import DailyBankrollAdvisor, DailyRecommendation
from bankroll_manager import BankrollManager, ContestInfo

logger = logging.getLogger(__name__)


@dataclass
class StrategicGuidance:
    """Complete strategic guidance for the day"""
    slate_size_recommendation: str
    optimal_contest_sizes: Dict[str, str]
    advanced_tips: List[str]
    market_timing: str
    risk_adjustments: List[str]
    performance_expectations: Dict[str, float]


class StrategicAdvisor:
    """Provides comprehensive strategic guidance for DFS"""
    
    def __init__(self, daily_advisor: DailyBankrollAdvisor):
        self.daily_advisor = daily_advisor
        
        # Strategy performance by slate size (from your testing)
        self.slate_performance = {
            'small': {
                'optimized_correlation_value': {'win_rate': 66.1, 'roi': 14.77},
                'projection_monster': {'win_rate': 45.0, 'roi': 116.94}
            },
            'medium': {
                'optimized_pitcher_dominance': {'win_rate': 71.6, 'roi': 12.90},
                'tournament_winner_gpp': {'win_rate': 42.5, 'roi': 90.14}
            },
            'large': {
                'optimized_tournament_winner_gpp': {'win_rate': 72.6, 'roi': 18.52},
                'correlation_value': {'win_rate': 37.7, 'roi': 85.0}
            }
        }
        
        # Contest size strategy (field size recommendations)
        self.contest_size_strategy = {
            'cash': {
                'small_field': "Head-to-Head, 3-max contests (easier to beat)",
                'medium_field': "50/50s, Double-ups (balanced risk/reward)",
                'large_field': "Avoid large cash games (harder to maintain edge)"
            },
            'gpp': {
                'small_field': "Avoid small GPPs (limited upside)",
                'medium_field': "Sweet spot for GPPs (good upside, manageable field)",
                'large_field': "Massive GPPs for huge upside (lower win rate but massive payouts)"
            }
        }
    
    def get_strategic_guidance(self, available_slates: List[str], 
                             bankroll: float, risk_level: str) -> StrategicGuidance:
        """Get comprehensive strategic guidance"""
        
        # Determine optimal slate size
        optimal_slate = self._recommend_slate_size(available_slates, bankroll, risk_level)
        
        # Get contest size recommendations
        contest_sizes = self._recommend_contest_sizes(bankroll, risk_level)
        
        # Generate advanced tips
        tips = self._generate_advanced_tips(optimal_slate, bankroll, risk_level)
        
        # Market timing advice
        timing = self._get_market_timing_advice(risk_level)
        
        # Risk adjustments
        adjustments = self._get_risk_adjustments(bankroll, risk_level)
        
        # Performance expectations
        expectations = self._calculate_performance_expectations(optimal_slate)
        
        return StrategicGuidance(
            slate_size_recommendation=optimal_slate,
            optimal_contest_sizes=contest_sizes,
            advanced_tips=tips,
            market_timing=timing,
            risk_adjustments=adjustments,
            performance_expectations=expectations
        )
    
    def _recommend_slate_size(self, available_slates: List[str], 
                            bankroll: float, risk_level: str) -> str:
        """Recommend optimal slate size based on bankroll and performance"""
        
        # Performance-based recommendations
        if bankroll < 200:
            # Small bankroll: Focus on highest win rate
            return "medium"  # 71.6% win rate with pitcher dominance
        elif bankroll < 1000:
            # Medium bankroll: Balance win rate and ROI
            if risk_level == "conservative":
                return "medium"  # Highest win rate (71.6%)
            else:
                return "large"   # Highest ROI (72.6% win rate, 18.52% ROI)
        else:
            # Large bankroll: Can handle variance for maximum ROI
            return "large"  # Best overall performance (72.6% win, 18.52% ROI)
    
    def _recommend_contest_sizes(self, bankroll: float, risk_level: str) -> Dict[str, str]:
        """Recommend optimal contest sizes (field sizes)"""
        
        recommendations = {}
        
        if risk_level == "conservative":
            recommendations['cash'] = "Small-Medium Fields (H2H, 3-max, small 50/50s)"
            recommendations['gpp'] = "Medium Fields (1K-5K entries for balanced risk/reward)"
        elif risk_level == "moderate":
            recommendations['cash'] = "Medium Fields (50/50s, Double-ups with 100-500 entries)"
            recommendations['gpp'] = "Medium-Large Fields (5K-20K entries for good upside)"
        else:  # aggressive
            recommendations['cash'] = "Any Size (focus on win rate over field size)"
            recommendations['gpp'] = "Large Fields (20K+ entries for maximum upside)"
        
        return recommendations
    
    def _generate_advanced_tips(self, slate_size: str, bankroll: float, 
                              risk_level: str) -> List[str]:
        """Generate advanced strategic tips"""
        
        tips = []
        
        # Slate-specific tips
        if slate_size == "small":
            tips.extend([
                "🎯 Small slates: Use Optimized Correlation Value strategy (66.1% win rate)",
                "⚡ Focus on elite Statcast players (barrel rate 15%+, xwOBA 0.360+)",
                "🏟️ Weather matters more on small slates - check wind/temperature",
                "👥 Lower ownership variance - focus on pure value plays"
            ])
        elif slate_size == "medium":
            tips.extend([
                "🎯 Medium slates: Use Optimized Pitcher Dominance strategy (71.6% win rate)",
                "⚾ Target elite K-rate pitchers (10.5+ K/9 for 1.25x boost)",
                "💰 Best balance of win rate and field size",
                "🎲 Moderate stacking opportunities (3-4 player stacks)"
            ])
        else:  # large
            tips.extend([
                "🎯 Large slates: Use Optimized Tournament Winner strategy (72.6% win rate)",
                "🏆 Highest ROI potential (18.52% average)",
                "📊 More stacking opportunities (4-5 player stacks)",
                "🎪 Higher variance but maximum upside"
            ])
        
        # Bankroll-specific tips
        if bankroll < 200:
            tips.extend([
                "💡 Small bankroll: Focus on cash games (higher win rates)",
                "🛡️ Limit GPP exposure to 20% of daily allocation",
                "📈 Build bankroll with consistent cash wins first"
            ])
        elif bankroll < 1000:
            tips.extend([
                "💡 Medium bankroll: 65% cash, 35% GPP allocation optimal",
                "🎯 Can handle moderate GPP variance",
                "📊 Track performance to optimize allocation"
            ])
        else:
            tips.extend([
                "💡 Large bankroll: Can maximize GPP upside",
                "🚀 Consider 50/50 cash/GPP split for maximum growth",
                "🎪 Can handle high-variance, high-upside plays"
            ])
        
        # Risk-specific tips
        if risk_level == "conservative":
            tips.extend([
                "🛡️ Conservative approach: Stick to proven high win rate plays",
                "💰 Focus on cash games and small-medium GPPs",
                "📉 Avoid high-variance tournament plays"
            ])
        elif risk_level == "aggressive":
            tips.extend([
                "🚀 Aggressive approach: Maximize upside potential",
                "🎪 Target large-field tournaments for massive payouts",
                "⚡ Can handle higher variance for higher rewards"
            ])
        
        return tips
    
    def _get_market_timing_advice(self, risk_level: str) -> str:
        """Get market timing recommendations"""
        
        if risk_level == "conservative":
            return "Enter contests early for better value, avoid late swap unless necessary"
        elif risk_level == "moderate":
            return "Mix of early entries and late swap opportunities based on news"
        else:
            return "Aggressive late swap strategy to exploit breaking news and ownership shifts"
    
    def _get_risk_adjustments(self, bankroll: float, risk_level: str) -> List[str]:
        """Get risk adjustment recommendations"""
        
        adjustments = []
        
        # Bankroll-based adjustments
        if bankroll < 100:
            adjustments.append("⚠️ Very small bankroll: Consider 5% daily limit instead of 10%")
        elif bankroll > 5000:
            adjustments.append("💪 Large bankroll: Can increase daily limit to 25% for growth")
        
        # Performance-based adjustments
        adjustments.extend([
            "📊 Track real performance vs projections weekly",
            "🔄 Adjust risk level based on recent results",
            "📈 Increase stakes after winning streaks, decrease after losses",
            "🎯 Never chase losses with increased stakes"
        ])
        
        return adjustments
    
    def _calculate_performance_expectations(self, slate_size: str) -> Dict[str, float]:
        """Calculate expected performance metrics"""
        
        if slate_size == "small":
            return {
                'daily_win_rate': 66.1,
                'weekly_profit_target': 15.0,  # % of bankroll
                'monthly_growth_target': 50.0,
                'variance_level': 'Low'
            }
        elif slate_size == "medium":
            return {
                'daily_win_rate': 71.6,
                'weekly_profit_target': 18.0,
                'monthly_growth_target': 65.0,
                'variance_level': 'Medium'
            }
        else:  # large
            return {
                'daily_win_rate': 72.6,
                'weekly_profit_target': 22.0,
                'monthly_growth_target': 80.0,
                'variance_level': 'Medium-High'
            }
    
    def format_strategic_guidance(self, guidance: StrategicGuidance, 
                                daily_rec: DailyRecommendation) -> str:
        """Format complete strategic guidance"""
        
        text = f"""
🧠 STRATEGIC GUIDANCE & RECOMMENDATIONS
{'=' * 60}

🎯 OPTIMAL SLATE SIZE: {guidance.slate_size_recommendation.upper()}
   Expected Win Rate: {guidance.performance_expectations['daily_win_rate']:.1f}%
   Weekly Profit Target: {guidance.performance_expectations['weekly_profit_target']:.1f}% of bankroll
   Monthly Growth Target: {guidance.performance_expectations['monthly_growth_target']:.1f}% of bankroll
   Variance Level: {guidance.performance_expectations['variance_level']}

🏟️ CONTEST SIZE STRATEGY:
   Cash Games: {guidance.optimal_contest_sizes['cash']}
   GPP Tournaments: {guidance.optimal_contest_sizes['gpp']}

⏰ MARKET TIMING:
   {guidance.market_timing}

🎯 ADVANCED STRATEGIC TIPS:
"""
        
        for i, tip in enumerate(guidance.advanced_tips, 1):
            text += f"   {tip}\n"
        
        text += f"""
⚠️ RISK ADJUSTMENTS:
"""
        
        for adjustment in guidance.risk_adjustments:
            text += f"   {adjustment}\n"
        
        text += f"""
📊 TODAY'S COMPLETE PLAN:
   Total Stake: ${daily_rec.total_daily_stake:.2f} ({daily_rec.bankroll_percentage:.1f}% of bankroll)
   Cash Allocation: ${daily_rec.cash_allocation:.2f}
   GPP Allocation: ${daily_rec.gpp_allocation:.2f}
   Expected Profit: ${daily_rec.expected_daily_profit:.2f}
   Risk Level: {daily_rec.risk_assessment}

💡 EXECUTION CHECKLIST:
   ✅ Check weather conditions for outdoor games
   ✅ Monitor late injury/lineup news
   ✅ Verify contest field sizes match recommendations
   ✅ Set lineup diversity for multiple GPP entries
   ✅ Track results vs projections for future optimization
"""
        
        return text


if __name__ == "__main__":
    print("🧠 STRATEGIC ADVISOR TEST")
    print("=" * 60)
    
    # Test strategic advisor
    from bankroll_manager import BankrollManager, RiskLevel
    
    manager = BankrollManager(500.0, RiskLevel.MODERATE)
    daily_advisor = DailyBankrollAdvisor(manager)
    strategic_advisor = StrategicAdvisor(daily_advisor)
    
    # Get strategic guidance
    guidance = strategic_advisor.get_strategic_guidance(
        ['small', 'medium', 'large'], 500.0, 'moderate'
    )
    
    # Get daily recommendation
    from daily_bankroll_advisor import SAMPLE_DAILY_CONTESTS
    daily_rec = daily_advisor.get_daily_recommendation(SAMPLE_DAILY_CONTESTS, 'medium')
    
    # Print complete guidance
    print(strategic_advisor.format_strategic_guidance(guidance, daily_rec))
    
    print("\n✅ Strategic Advisor ready for integration!")
