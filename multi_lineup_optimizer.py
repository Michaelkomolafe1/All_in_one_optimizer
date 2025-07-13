"""
Multi-Lineup Optimizer for DFS
Generate 20-150 unique lineups with exposure and ownership controls
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class MultiLineupOptimizer:
    """Generate multiple unique lineups for GPPs with WORKING diversity"""

    def __init__(self, core_optimizer):
        self.core = core_optimizer
        self.generated_lineups = []
        self.lineup_hashes = set()
        self.player_exposure = {}

    def generate_gpp_lineups(
        self, num_lineups: int = 20, max_exposure: float = 0.5, min_salary: int = 49000
    ) -> List[Tuple]:
        """Generate unique lineups with proper diversity control"""
        print(f"\n🚀 Generating {num_lineups} unique GPP lineups...")
        print(f"   Max exposure: {max_exposure * 100:.0f}%")
        print(f"   Min salary: ${min_salary:,}")

        # Reset tracking
        self.generated_lineups = []
        self.lineup_hashes = set()
        self.player_exposure = {}

        successful = 0
        attempts = 0
        max_attempts = num_lineups * 3

        while successful < num_lineups and attempts < max_attempts:
            attempts += 1

            # Get lineup using core's diversity method
            lineups = self.core.generate_contest_lineups(
                count=1,  # One at a time for better diversity
                contest_type="gpp",
                max_exposure=max_exposure,
                diversity_factor=0.7
                + (successful / num_lineups) * 0.3,  # Increase diversity over time
            )

            if lineups and self._is_unique_lineup(lineups[0]["lineup"]):
                lineup_data = (lineups[0]["lineup"], lineups[0]["total_score"], lineups[0])

                self.generated_lineups.append(lineup_data)
                self._update_exposure(lineups[0]["lineup"])
                successful += 1

                if successful % 5 == 0:
                    print(f"   Generated {successful}/{num_lineups} lineups...")

        # Sort by score
        self.generated_lineups.sort(key=lambda x: x[1], reverse=True)

        print(f"\n✅ Successfully generated {len(self.generated_lineups)} unique lineups")

        # Show exposure report
        self._print_exposure_summary(max_exposure)

        return self.generated_lineups

    def _print_exposure_summary(self, max_exposure: float):
        """Print summary of player exposure"""
        if not self.generated_lineups:
            return

        total_lineups = len(self.generated_lineups)
        overexposed = []

        print("\n📊 Top Player Exposure:")
        sorted_exposure = sorted(self.player_exposure.items(), key=lambda x: x[1], reverse=True)

        for player_id, count in sorted_exposure[:10]:
            exposure = count / total_lineups
            # Find player name
            player_name = "Unknown"
            for lineup, _, _ in self.generated_lineups:
                for p in lineup:
                    if p.id == player_id:
                        player_name = p.name
                        break
                if player_name != "Unknown":
                    break

            status = "⚠️" if exposure > max_exposure else "✅"
            print(f"   {status} {player_name}: {exposure * 100:.1f}% ({count}/{total_lineups})")

            if exposure > max_exposure:
                overexposed.append(player_name)

        if overexposed:
            print(f"\n⚠️ Warning: {len(overexposed)} players exceed max exposure")

    def _get_strategy_distribution(self, num_lineups: int) -> List[str]:
        """Get strategy distribution for lineups"""
        if num_lineups <= 3:
            return ["balanced"] * num_lineups
        elif num_lineups <= 20:
            # 20 lineup distribution
            return (
                ["balanced"] * int(num_lineups * 0.4)
                + ["contrarian"] * int(num_lineups * 0.3)
                + ["stacks"] * int(num_lineups * 0.2)
                + ["value"] * int(num_lineups * 0.1)
            )
        else:
            # 150 lineup distribution
            return (
                ["balanced"] * int(num_lineups * 0.3)
                + ["contrarian"] * int(num_lineups * 0.25)
                + ["stacks"] * int(num_lineups * 0.25)
                + ["value"] * int(num_lineups * 0.1)
                + ["high_upside"] * int(num_lineups * 0.1)
            )

    def _generate_single_lineup(
        self, strategy: str, current: int, total: int, max_exp: float, min_sal: int
    ) -> Optional[Tuple]:
        """Generate a single lineup with given strategy"""

        # Get eligible players
        eligible = self.core.get_eligible_players_by_mode()
        if not eligible:
            return None

        # Apply strategy adjustments
        self._apply_strategy_adjustments(eligible, strategy, current, total, max_exp)

        # Store original scores
        original_scores = {}
        for player in eligible:
            original_scores[player.name] = player.enhanced_score

        try:
            # Generate lineup
            lineup, score = self.core.optimize_lineup_with_mode()

            if not lineup:
                return None

            # Check salary
            total_salary = sum(p.salary for p in lineup)
            if total_salary < min_sal:
                return None

            # Calculate metadata
            metadata = {
                "strategy": strategy,
                "salary": total_salary,
                "ownership": sum(getattr(p, "ownership", 0) for p in lineup),
                "num_stacks": self._count_stacks(lineup),
            }

            return (lineup, score, metadata)

        finally:
            # Restore original scores
            for player in eligible:
                if player.name in original_scores:
                    player.enhanced_score = original_scores[player.name]

    def _apply_strategy_adjustments(
        self, players: List, strategy: str, current: int, total: int, max_exp: float
    ):
        """Apply strategy-specific score adjustments"""

        for player in players:
            # Base score
            base_score = player.enhanced_score

            # Exposure penalty
            exposure = self.player_exposure.get(player.name, 0) / max(current, 1)
            if exposure > max_exp:
                penalty = min(0.5, (exposure - max_exp) * 2)
                base_score *= 1 - penalty

            # Strategy adjustments
            if strategy == "contrarian":
                # Boost low ownership
                if hasattr(player, "ownership"):
                    if player.ownership < 10:
                        base_score *= 1.15
                    elif player.ownership > 25:
                        base_score *= 0.85

            elif strategy == "stacks":
                # This would need team correlation logic
                # For now, slight randomization
                base_score *= random.uniform(0.95, 1.05)

            elif strategy == "value":
                # Boost value plays
                value = base_score / (player.salary / 1000)
                if value > 3.0:  # Good value
                    base_score *= 1.1

            elif strategy == "high_upside":
                # Boost high ceiling players
                if hasattr(player, "ceiling") and player.ceiling > base_score * 1.5:
                    base_score *= 1.1

            # Apply adjusted score
            player.enhanced_score = base_score

    def _is_unique_lineup(self, lineup: List) -> bool:
        """Check if lineup is unique"""
        # Create hash from sorted player names
        player_names = sorted([p.name for p in lineup])
        lineup_hash = hash(tuple(player_names))

        if lineup_hash in self.lineup_hashes:
            return False

        self.lineup_hashes.add(lineup_hash)
        return True

    def _update_exposure(self, lineup: List):
        """Update player exposure tracking"""
        for player in lineup:
            self.player_exposure[player.name] = self.player_exposure.get(player.name, 0) + 1

    def _count_stacks(self, lineup: List) -> int:
        """Count team stacks in lineup"""
        team_counts = {}
        for player in lineup:
            if player.primary_position != "P":  # Don't count pitchers
                team_counts[player.team] = team_counts.get(player.team, 0) + 1

        # Count teams with 3+ players as stacks
        return sum(1 for count in team_counts.values() if count >= 3)

    def export_for_upload(self, site: str = "draftkings") -> str:
        """Export lineups for site upload"""
        if not self.generated_lineups:
            print("❌ No lineups to export")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        if site.lower() == "draftkings":
            filename = f"dk_upload_{timestamp}.csv"

            with open(filename, "w") as f:
                # DraftKings wants player IDs only
                for lineup, score, meta in self.generated_lineups:
                    # Sort by DK position order
                    positions = ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"]
                    sorted_lineup = []

                    for pos in positions:
                        for p in lineup:
                            if p.primary_position == pos and p not in sorted_lineup:
                                sorted_lineup.append(p)
                                break

                    # Write IDs
                    ids = [str(getattr(p, "id", "")) for p in sorted_lineup]
                    f.write(",".join(ids) + "\n")

            print(f"📁 Saved DraftKings upload file: {filename}")
            return filename

        return ""

    def get_exposure_report(self) -> Dict:
        """Get player exposure report"""
        if not self.generated_lineups:
            return {}

        total_lineups = len(self.generated_lineups)

        exposure_report = {}
        for player, count in self.player_exposure.items():
            exposure_report[player] = {"count": count, "percentage": (count / total_lineups) * 100}

        # Sort by exposure
        sorted_exposure = dict(
            sorted(exposure_report.items(), key=lambda x: x[1]["percentage"], reverse=True)
        )

        return sorted_exposure

    def print_summary(self):
        """Print summary of generated lineups"""
        if not self.generated_lineups:
            print("No lineups generated")
            return

        print(f"\n📊 LINEUP GENERATION SUMMARY")
        print("=" * 50)

        # Basic stats
        scores = [score for _, score, _ in self.generated_lineups]
        print(f"Total lineups: {len(self.generated_lineups)}")
        print(f"Score range: {min(scores):.2f} - {max(scores):.2f}")
        print(f"Average score: {sum(scores)/len(scores):.2f}")

        # Strategy breakdown
        strategy_counts = {}
        for _, _, meta in self.generated_lineups:
            strat = meta["strategy"]
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

        print(f"\nStrategy distribution:")
        for strat, count in strategy_counts.items():
            print(f"  {strat}: {count} lineups")

        # Top exposure
        exposure = self.get_exposure_report()
        print(f"\nTop 10 player exposure:")
        for i, (player, data) in enumerate(list(exposure.items())[:10]):
            print(f"  {player}: {data['percentage']:.1f}% ({data['count']} lineups)")
