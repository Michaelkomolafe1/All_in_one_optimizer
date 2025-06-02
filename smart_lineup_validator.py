#!/usr/bin/env python3
"""
Smart Lineup Validator Module - FIXED VERSION
============================================
Real-time lineup validation and smart suggestions with all references resolved
"""

from typing import List, Dict, Optional, Tuple, Any

class SmartLineupValidator:
    """Smart lineup validation with real-time feedback"""

    def __init__(self, salary_cap: int = 50000):
        self.salary_cap = salary_cap
        self.position_requirements = {
            'P': 2,    # 2 Pitchers
            'C': 1,    # 1 Catcher  
            '1B': 1,   # 1 First Base
            '2B': 1,   # 1 Second Base
            '3B': 1,   # 1 Third Base
            'SS': 1,   # 1 Shortstop
            'OF': 3    # 3 Outfielders
        }
        self.max_players = 10

    def validate_lineup(self, selected_players: List) -> Dict:
        """Main validation function - returns comprehensive analysis"""

        if not selected_players:
            return self._create_empty_lineup_result()

        # Initialize validation result
        result = {
            'is_valid': True,
            'is_complete': False,
            'issues': [],
            'warnings': [],
            'suggestions': [],
            'salary_analysis': {},
            'position_analysis': {},
            'player_count': len(selected_players),
            'spots_remaining': max(0, self.max_players - len(selected_players))
        }

        # Analyze salary usage
        salary_analysis = self._analyze_salary_usage(selected_players)
        result['salary_analysis'] = salary_analysis

        # Check for salary cap violations
        if salary_analysis['over_cap']:
            result['is_valid'] = False
            result['issues'].append(f"Over salary cap by ${salary_analysis['over_amount']:,}")

        # Analyze position requirements
        position_analysis = self._analyze_position_requirements(selected_players)
        result['position_analysis'] = position_analysis

        # Check for missing positions
        if position_analysis['positions_missing']:
            result['is_valid'] = False
            for pos, count in position_analysis['positions_missing'].items():
                result['issues'].append(f"Missing {count} {pos} player(s)")

        # Check player count
        player_count = len(selected_players)
        if player_count > self.max_players:
            result['is_valid'] = False
            result['issues'].append(f"Too many players: {player_count}/{self.max_players}")
        elif player_count == self.max_players:
            result['is_complete'] = True
            if result['is_valid']:
                result['suggestions'].append("✅ Lineup is complete and valid!")
        else:
            needed = self.max_players - player_count
            result['suggestions'].append(f"Need {needed} more player(s) to complete lineup")

        # Add correlation warnings
        correlation_warnings = self._check_correlation_risks(selected_players)
        result['warnings'].extend(correlation_warnings)

        # Generate completion suggestions if lineup isn't complete
        if not result['is_complete'] and result['is_valid']:
            completion_suggestions = self._generate_completion_suggestions(
                selected_players, salary_analysis, position_analysis
            )
            result['suggestions'].extend(completion_suggestions)

        return result

    def _create_empty_lineup_result(self) -> Dict:
        """Create result for empty lineup"""
        return {
            'is_valid': False,
            'is_complete': False,
            'issues': ['No players selected'],
            'warnings': [],
            'suggestions': [
                'Start by selecting your favorite 3-4 players',
                f'You have ${self.salary_cap:,} salary cap to work with',
                'Try using enhanced selection: "vlad jr, all astros hitters"'
            ],
            'salary_analysis': {
                'total_used': 0,
                'remaining': self.salary_cap,
                'over_cap': False,
                'avg_per_player': 0
            },
            'position_analysis': {
                'positions_filled': {},
                'positions_missing': self.position_requirements.copy()
            },
            'player_count': 0,
            'spots_remaining': self.max_players
        }

    def _analyze_salary_usage(self, selected_players: List) -> Dict:
        """Analyze salary cap usage"""
        total_salary = 0

        for player in selected_players:
            if hasattr(player, 'salary'):
                total_salary += player.salary

        remaining = self.salary_cap - total_salary
        avg_per_player = total_salary / len(selected_players) if selected_players else 0

        return {
            'total_used': total_salary,
            'remaining': remaining,
            'over_cap': total_salary > self.salary_cap,
            'over_amount': max(0, total_salary - self.salary_cap),
            'avg_per_player': avg_per_player,
            'percentage_used': (total_salary / self.salary_cap) * 100
        }

    def _analyze_position_requirements(self, selected_players: List) -> Dict:
        """Analyze position requirements and gaps"""
        positions_filled = {}

        # Count current positions
        for player in selected_players:
            if hasattr(player, 'primary_position'):
                pos = player.primary_position
                positions_filled[pos] = positions_filled.get(pos, 0) + 1
            elif hasattr(player, 'positions') and player.positions:
                # Use first position if primary_position doesn't exist
                pos = player.positions[0]
                positions_filled[pos] = positions_filled.get(pos, 0) + 1

        # Calculate missing positions
        positions_missing = {}
        for pos, required in self.position_requirements.items():
            current = positions_filled.get(pos, 0)
            if current < required:
                positions_missing[pos] = required - current

        return {
            'positions_filled': positions_filled,
            'positions_missing': positions_missing,
            'total_filled': sum(positions_filled.values()),
            'total_missing': sum(positions_missing.values())
        }

    def _check_correlation_risks(self, selected_players: List) -> List[str]:
        """Check for correlation risks (too many players from same team)"""
        warnings = []
        team_counts = {}

        for player in selected_players:
            if hasattr(player, 'team'):
                team = player.team
                team_counts[team] = team_counts.get(team, 0) + 1

        # Flag teams with 4+ players (high correlation)
        for team, count in team_counts.items():
            if count >= 4:
                warnings.append(f"High correlation risk: {count} players from {team}")
            elif count == 3:
                warnings.append(f"Moderate correlation: {count} players from {team}")

        return warnings

    def _generate_completion_suggestions(self, selected_players: List, 
                                       salary_analysis: Dict, position_analysis: Dict) -> List[str]:
        """Generate smart suggestions to complete the lineup"""
        suggestions = []

        remaining_salary = salary_analysis['remaining']
        spots_remaining = self.max_players - len(selected_players)
        positions_missing = position_analysis['positions_missing']

        if spots_remaining <= 0:
            return suggestions

        # Calculate budget per remaining spot
        budget_per_spot = remaining_salary / spots_remaining if spots_remaining > 0 else 0

        # Position-specific guidance
        if positions_missing:
            for pos, count in positions_missing.items():
                if count > 0:
                    if budget_per_spot >= 4000:
                        suggestions.append(f"Fill {pos} position - budget ${budget_per_spot:,.0f} per spot")
                    else:
                        suggestions.append(f"Need {pos} - look for value plays under ${budget_per_spot:,.0f}")

        # Budget guidance
        if budget_per_spot > 6000:
            suggestions.append("High budget remaining - consider premium players")
        elif budget_per_spot < 3500:
            suggestions.append("Tight budget - focus on minimum salary players")
        elif budget_per_spot < 4500:
            suggestions.append("Medium budget - look for value plays")

        # General completion guidance
        if not positions_missing:
            suggestions.append("All positions filled - focus on best available value")

        return suggestions

    def get_lineup_summary(self, selected_players: List) -> str:
        """Get a formatted summary of current lineup status"""
        validation = self.validate_lineup(selected_players)

        lines = []
        lines.append("📊 LINEUP SUMMARY")
        lines.append("=" * 30)

        # Status
        if validation['is_complete'] and validation['is_valid']:
            lines.append("Status: ✅ COMPLETE & VALID")
        elif validation['is_valid']:
            lines.append("Status: 🟡 VALID (Incomplete)")
        else:
            lines.append("Status: ❌ INVALID")

        # Player count
        lines.append(f"Players: {validation['player_count']}/{self.max_players}")

        # Salary
        salary = validation['salary_analysis']
        lines.append(f"Salary: ${salary['total_used']:,} / ${self.salary_cap:,}")
        lines.append(f"Remaining: ${salary['remaining']:,}")

        # Positions
        positions = validation['position_analysis']['positions_filled']
        if positions:
            pos_summary = []
            for pos, count in positions.items():
                required = self.position_requirements.get(pos, 0)
                if count >= required:
                    pos_summary.append(f"{pos}:✅{count}")
                else:
                    pos_summary.append(f"{pos}:❌{count}/{required}")
            lines.append(f"Positions: {' '.join(pos_summary)}")

        # Issues
        if validation['issues']:
            lines.append("")
            lines.append("🚨 Issues:")
            for issue in validation['issues']:
                lines.append(f"  • {issue}")

        # Top suggestions
        if validation['suggestions']:
            lines.append("")
            lines.append("💡 Suggestions:")
            for suggestion in validation['suggestions'][:3]:  # Show top 3
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)


def get_value_recommendations(selected_players: List, available_players: List, 
                            max_recs: int = 5) -> List[Dict]:
    """Get value-based player recommendations (standalone function)"""

    if not available_players:
        return []

    # Get players not already selected
    available_names = set()
    if selected_players:
        available_names = {getattr(p, 'name', str(p)) for p in selected_players}

    recommendations = []

    for player in available_players:
        # Skip if already selected
        player_name = getattr(player, 'name', str(player))
        if player_name in available_names:
            continue

        # Calculate value score
        salary = getattr(player, 'salary', 1)
        score = getattr(player, 'enhanced_score', 0)

        if salary > 0:
            value_score = score / (salary / 1000)  # Points per $1K

            recommendations.append({
                'player_name': player_name,
                'position': getattr(player, 'primary_position', 'Unknown'),
                'salary': salary,
                'projected_score': score,
                'value_score': value_score,
                'player_object': player
            })

    # Sort by value score
    recommendations.sort(key=lambda x: x['value_score'], reverse=True)

    return recommendations[:max_recs]
