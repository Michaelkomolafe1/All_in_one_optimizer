"""
Simple ownership projection system for DFS
"""


class OwnershipProjector:
    """Project ownership based on salary, projections, and narratives"""

    @staticmethod
    def calculate_ownership(player, all_players):
        """
        Calculate projected ownership percentage

        Factors:
        - Salary rank
        - Projection rank
        - Team Vegas total
        - Recent performance
        - Narrative/chalk factors
        """
        # Get player's percentile ranks
        salary_rank = sum(1 for p in all_players if p.salary > player.salary) / len(all_players)
        proj_rank = sum(
            1 for p in all_players if getattr(p, 'base_projection', 0) > getattr(player, 'base_projection', 0)) / len(
            all_players)

        # Base ownership from ranks (top players get owned more)
        base_own = (1 - salary_rank) * 0.4 + (1 - proj_rank) * 0.6

        # Adjustments
        multiplier = 1.0

        # Position adjustments
        if player.is_pitcher:
            if player.salary >= 10000:  # Ace pitcher
                multiplier *= 1.5
            if getattr(player, 'opponent_implied_total', 4.5) <= 3.5:  # Good matchup
                multiplier *= 1.3
        else:
            # Hitters
            if getattr(player, 'batting_order', 0) in [1, 2, 3, 4]:
                multiplier *= 1.2
            if getattr(player, 'team_total', 4.5) >= 5.5:  # High scoring game
                multiplier *= 1.3

        # Team popularity
        chalk_teams = {'NYY', 'LAD', 'HOU', 'BOS', 'ATL'}
        if player.team in chalk_teams:
            multiplier *= 1.25

        # Min price value plays get owned heavily
        if player.salary <= 3000 and getattr(player, 'base_projection', 0) >= 6:
            multiplier *= 2.0

        # Calculate final ownership (1-40% range typically)
        ownership = min(40, max(1, base_own * multiplier * 35))

        return round(ownership, 1)