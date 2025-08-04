#!/usr/bin/env python3
"""
Enhanced GUI Display Components
Shows all score types and enrichment details
"""


class EnhancedGUIDisplay:
    """Enhanced display for DFS optimizer GUI"""

    @staticmethod
    def format_player_display(player, contest_type='cash'):
        """Format player for GUI display with all scores"""
        # Determine which score to use for optimization
        if contest_type == 'cash':
            opt_score = player.cash_score
        else:
            opt_score = player.gpp_score

        return {
            'name': player.name,
            'position': player.primary_position,
            'team': player.team,
            'salary': player.salary,
            'salary_display': f"${player.salary:,}",

            # All score types
            'dk_projection': round(player.base_projection, 1),  # Original DK projection
            'enhanced_score': round(player.enhanced_score, 1),  # After enrichments
            'cash_score': round(player.cash_score, 1),  # Conservative score
            'gpp_score': round(player.gpp_score, 1),  # Aggressive score
            'optimization_score': round(opt_score, 1),  # Score being used

            # Enhancement details
            'vegas_mult': round(getattr(player, 'vegas_score', 1.0), 2),
            'park_mult': round(getattr(player, 'park_score', 1.0), 2),
            'weather_mult': round(getattr(player, 'weather_score', 1.0), 2),
            'matchup_mult': round(getattr(player, 'matchup_score', 1.0), 2),

            # Impact metrics
            'enhancement_impact': round(player.enhanced_score - player.base_projection, 1),
            'enhancement_pct': round((player.enhanced_score - player.base_projection) / player.base_projection * 100,
                                     1) if player.base_projection > 0 else 0,

            # Value metrics
            'dk_value': round(player.base_projection / (player.salary / 1000), 2) if player.salary > 0 else 0,
            'enhanced_value': round(player.enhanced_score / (player.salary / 1000), 2) if player.salary > 0 else 0,
            'opt_value': round(opt_score / (player.salary / 1000), 2) if player.salary > 0 else 0,

            # Display string for GUI
            'display_string': f"{player.name} ({player.team}) - ${player.salary} - {opt_score:.1f} pts"
        }

    @staticmethod
    def create_lineup_display(lineup, contest_type='cash'):
        """Create comprehensive lineup display"""
        players = lineup['players']

        # Calculate all totals
        totals = {
            'salary': sum(p.salary for p in players),
            'dk_projection': sum(p.base_projection for p in players),
            'enhanced_total': sum(p.enhanced_score for p in players),
            'cash_total': sum(p.cash_score for p in players),
            'gpp_total': sum(p.gpp_score for p in players),
        }

        # Format each player
        player_displays = []
        for p in players:
            display = EnhancedGUIDisplay.format_player_display(p, contest_type)
            player_displays.append(display)

        return {
            'players': player_displays,
            'totals': totals,
            'contest_type': contest_type,
            'optimization_score': totals['cash_total'] if contest_type == 'cash' else totals['gpp_total'],
            'salary_remaining': 50000 - totals['salary']
        }

    @staticmethod
    def get_score_breakdown_text(player):
        """Get detailed text explanation of scoring"""
        lines = []
        lines.append(f"🎯 {player.name} Score Breakdown:")
        lines.append(f"")
        lines.append(f"DraftKings Projection: {player.base_projection:.1f} pts")
        lines.append(f"")
        lines.append(f"Enhancement Factors:")
        lines.append(f"  × Vegas: {getattr(player, 'vegas_score', 1.0):.2f}")
        lines.append(f"  × Park: {getattr(player, 'park_score', 1.0):.2f}")
        lines.append(f"  × Weather: {getattr(player, 'weather_score', 1.0):.2f}")
        lines.append(f"  × Matchup: {getattr(player, 'matchup_score', 1.0):.2f}")
        lines.append(f"  = Enhanced: {player.enhanced_score:.1f} pts")
        lines.append(f"")
        lines.append(f"Contest Scores:")
        lines.append(f"  Cash (safe): {player.cash_score:.1f} pts")
        lines.append(f"  GPP (upside): {player.gpp_score:.1f} pts")

        return "\n".join(lines)

    @staticmethod
    def format_for_gui_table(players, contest_type='cash'):
        """Format players for GUI table/list display"""
        rows = []
        for player in players:
            display = EnhancedGUIDisplay.format_player_display(player, contest_type)

            # Create row for GUI table
            row = {
                'Position': player.primary_position,
                'Name': player.name,
                'Team': player.team,
                'Salary': display['salary_display'],
                'DK Proj': f"{display['dk_projection']:.1f}",
                'Enhanced': f"{display['enhanced_score']:.1f}",
                'Score': f"{display['optimization_score']:.1f}",
                'Value': f"{display['opt_value']:.2f}",
                # Hidden data for sorting
                '_salary': player.salary,
                '_score': display['optimization_score'],
                '_value': display['opt_value'],
                # Full player object for details
                '_player': player
            }
            rows.append(row)

        return rows


# Example usage in your GUI
def example_gui_update(system, lineup, contest_type='cash'):
    """Example of how to update your GUI"""

    # Format lineup for display
    lineup_display = EnhancedGUIDisplay.create_lineup_display(lineup, contest_type)

    print(f"\n📊 ENHANCED LINEUP DISPLAY ({contest_type.upper()}):")
    print("=" * 90)
    print(f"{'Pos':<4} {'Player':<20} {'Team':<4} {'Salary':<8} {'DK':<6} {'Enh':<6} {'Cash':<6} {'GPP':<6} {'Use':<6}")
    print("-" * 90)

    for p_data in lineup_display['players']:
        print(f"{p_data['position']:<4} {p_data['name']:<20} {p_data['team']:<4} "
              f"{p_data['salary_display']:<8} {p_data['dk_projection']:<6.1f} "
              f"{p_data['enhanced_score']:<6.1f} {p_data['cash_score']:<6.1f} "
              f"{p_data['gpp_score']:<6.1f} {p_data['optimization_score']:<6.1f}")

    print("-" * 90)
    totals = lineup_display['totals']
    print(f"{'TOTALS:':<37} ${totals['salary']:<7,} "
          f"{totals['dk_projection']:<6.1f} {totals['enhanced_total']:<6.1f} "
          f"{totals['cash_total']:<6.1f} {totals['gpp_total']:<6.1f} "
          f"{lineup_display['optimization_score']:<6.1f}")

    print(f"\nSalary Remaining: ${lineup_display['salary_remaining']:,}")

    # Show enhancement impact
    enhancement_impact = totals['enhanced_total'] - totals['dk_projection']
    print(f"Enhancement Impact: {enhancement_impact:+.1f} pts "
          f"({enhancement_impact / totals['dk_projection'] * 100:+.1f}%)")


if __name__ == "__main__":
    print("Enhanced GUI Display Component")
    print("Import this in your GUI to show all score types")