#!/usr/bin/env python3
"""
SCALING TRACKER
===============
Track progression toward $50 daily stakes and $400 bankroll target
Shows realistic timeline and milestones
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class ScalingMilestone:
    """Milestone in scaling progression"""
    day: int
    bankroll: float
    daily_stake: float
    weekly_profit: float
    time_to_target: str


class ScalingTracker:
    """Track progression toward bankroll and stake targets"""
    
    def __init__(self, starting_bankroll: float = 130.0, target_bankroll: float = 400.0, 
                 target_daily_stake: float = 50.0):
        self.starting_bankroll = starting_bankroll
        self.target_bankroll = target_bankroll
        self.target_daily_stake = target_daily_stake
        
        # Scaling parameters (25% daily limit)
        self.daily_percentage = 0.25  # 25% of bankroll daily
        self.cash_allocation = 0.75   # 75% cash focus
        self.expected_daily_roi = 0.15  # 15% daily ROI (conservative estimate)
        
    def calculate_scaling_progression(self, days: int = 90) -> List[ScalingMilestone]:
        """Calculate day-by-day progression"""
        
        milestones = []
        bankroll = self.starting_bankroll
        
        for day in range(1, days + 1):
            # Calculate daily stake (25% of current bankroll)
            daily_stake = bankroll * self.daily_percentage
            
            # Calculate expected daily profit
            daily_profit = daily_stake * self.expected_daily_roi
            
            # Update bankroll
            bankroll += daily_profit
            
            # Calculate weekly profit (for milestone tracking)
            weekly_profit = daily_profit * 7
            
            # Check if we've reached targets
            if daily_stake >= self.target_daily_stake and bankroll >= self.target_bankroll:
                time_to_target = f"ACHIEVED on day {day}!"
            elif daily_stake >= self.target_daily_stake:
                time_to_target = f"$50 stakes achieved, ${self.target_bankroll:.0f} in {self._days_to_target(bankroll, self.target_bankroll):.0f} days"
            elif bankroll >= self.target_bankroll:
                time_to_target = f"${self.target_bankroll:.0f} achieved, $50 stakes in {self._days_to_50_stakes(bankroll):.0f} days"
            else:
                days_to_50 = self._days_to_50_stakes(bankroll)
                days_to_400 = self._days_to_target(bankroll, self.target_bankroll)
                time_to_target = f"$50 stakes: {days_to_50:.0f}d, $400: {days_to_400:.0f}d"
            
            # Store milestone every 7 days or at key points
            if day % 7 == 0 or daily_stake >= 25 or daily_stake >= 40 or daily_stake >= 50:
                milestones.append(ScalingMilestone(
                    day=day,
                    bankroll=bankroll,
                    daily_stake=daily_stake,
                    weekly_profit=weekly_profit,
                    time_to_target=time_to_target
                ))
            
            # Stop if we've achieved both targets
            if daily_stake >= self.target_daily_stake and bankroll >= self.target_bankroll:
                break
        
        return milestones
    
    def _days_to_50_stakes(self, current_bankroll: float) -> float:
        """Calculate days to reach $50 daily stakes"""
        target_bankroll_for_50 = self.target_daily_stake / self.daily_percentage  # $200
        if current_bankroll >= target_bankroll_for_50:
            return 0
        
        # Use compound growth formula
        daily_growth_rate = self.daily_percentage * self.expected_daily_roi
        return math.log(target_bankroll_for_50 / current_bankroll) / math.log(1 + daily_growth_rate)
    
    def _days_to_target(self, current_bankroll: float, target: float) -> float:
        """Calculate days to reach target bankroll"""
        if current_bankroll >= target:
            return 0
        
        daily_growth_rate = self.daily_percentage * self.expected_daily_roi
        return math.log(target / current_bankroll) / math.log(1 + daily_growth_rate)
    
    def get_scaling_summary(self) -> Dict:
        """Get summary of scaling approach"""
        
        milestones = self.calculate_scaling_progression()
        
        # Find key milestones
        day_50_stakes = None
        day_400_bankroll = None
        
        for milestone in milestones:
            if milestone.daily_stake >= 50 and day_50_stakes is None:
                day_50_stakes = milestone.day
            if milestone.bankroll >= 400 and day_400_bankroll is None:
                day_400_bankroll = milestone.day
        
        return {
            'starting_bankroll': self.starting_bankroll,
            'target_bankroll': self.target_bankroll,
            'target_daily_stake': self.target_daily_stake,
            'daily_percentage': self.daily_percentage * 100,
            'cash_allocation': self.cash_allocation * 100,
            'expected_daily_roi': self.expected_daily_roi * 100,
            'days_to_50_stakes': day_50_stakes,
            'days_to_400_bankroll': day_400_bankroll,
            'milestones': milestones[:10]  # First 10 milestones
        }
    
    def format_scaling_plan(self) -> str:
        """Format scaling plan as readable text"""
        
        summary = self.get_scaling_summary()
        milestones = summary['milestones']
        
        text = f"""
🚀 AGGRESSIVE BUT SAFE SCALING PLAN
{'=' * 60}

🎯 TARGETS:
   Target Bankroll: ${summary['target_bankroll']:.0f}
   Target Daily Stake: ${summary['target_daily_stake']:.0f}
   
📊 SCALING APPROACH:
   Daily Risk: {summary['daily_percentage']:.0f}% of current bankroll
   Cash Focus: {summary['cash_allocation']:.0f}% allocation
   Expected Daily ROI: {summary['expected_daily_roi']:.0f}%
   
⏰ TIMELINE:
   Reach $50 daily stakes: ~{summary['days_to_50_stakes']} days
   Reach $400 bankroll: ~{summary['days_to_400_bankroll']} days
   
📈 PROGRESSION MILESTONES:
"""
        
        for milestone in milestones:
            text += f"""
   Day {milestone.day:2d}: ${milestone.bankroll:6.0f} bankroll → ${milestone.daily_stake:5.1f} daily stake
           Weekly profit: ${milestone.weekly_profit:5.1f} | {milestone.time_to_target}"""
        
        text += f"""

💡 KEY ADVANTAGES:
   ✅ Scales naturally - no fixed $50 risk when bankroll is small
   ✅ Reaches $50 stakes when bankroll can handle it (~$200)
   ✅ 75% cash focus for consistency and growth
   ✅ 25% daily limit is aggressive but manageable
   ✅ Compound growth accelerates progress

⚠️ IMPORTANT NOTES:
   • Start with Aggressive risk level in your GUI
   • Focus on 50/50s and double-ups (highest win rates)
   • Track real performance vs these projections
   • Adjust if actual ROI differs from 15% expectation
   • Never exceed 25% daily limit even if tempted

🎯 EXECUTION:
   1. Set GUI to "Aggressive" risk level
   2. Use daily recommendations (will be ~25% of bankroll)
   3. Focus on cash games (75% allocation)
   4. Track progress weekly
   5. Celebrate milestones!
"""
        
        return text


if __name__ == "__main__":
    print("🚀 SCALING TRACKER TEST")
    print("=" * 50)
    
    # Test scaling tracker
    tracker = ScalingTracker(130.0, 400.0, 50.0)
    
    # Get and display scaling plan
    plan = tracker.format_scaling_plan()
    print(plan)
    
    print("\n✅ Scaling tracker ready for integration!")
