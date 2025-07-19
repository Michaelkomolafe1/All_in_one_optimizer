#!/usr/bin/env python3
"""
INTEGRATED STATCAST RECENT FORM
===============================
Designed to work seamlessly with your unified scoring engine
No competing calculations - integrates perfectly
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class IntegratedStatcastRecentForm:
    """
    Statcast recent form that integrates with your UnifiedScoringEngine
    Sets the _recent_performance attribute that your system expects
    """

    def __init__(self, statcast_fetcher=None, days_back=7):
        """
        Initialize with existing statcast fetcher if available

        Args:
            statcast_fetcher: Your existing FastStatcastFetcher instance
            days_back: How many days to look back (default 7)
        """
        self.statcast_fetcher = statcast_fetcher
        self.days_back = days_back
        self.cache_dir = Path("data/statcast_recent_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def enrich_players_with_recent_form(self, players: List) -> int:
        """
        Main method to enrich players with recent form
        This is called from your core system
        """
        print(f"\n📊 ENRICHING {len(players)} PLAYERS WITH STATCAST RECENT FORM")
        print("=" * 60)

        if not self.statcast_fetcher:
            print("❌ No Statcast fetcher available")
            return 0

        enriched_count = 0

        for i, player in enumerate(players):
            # Skip if already has recent form
            if hasattr(player, '_recent_performance') and player._recent_performance:
                if player._recent_performance.get('source') == 'statcast_recent':
                    continue

            # Show progress for first 10
            if i < 10:
                print(f"  Processing {player.name}...", end=" ")

            try:
                # Get recent stats using existing fetcher
                position = "P" if getattr(player, 'primary_position', '') == 'P' else "H"

                # Use the fetcher's existing methods
                if position == "P":
                    stats = self.statcast_fetcher.get_pitcher_stats(player.name)
                else:
                    stats = self.statcast_fetcher.get_hitter_stats(player.name)

                if stats:
                    # Convert Statcast data to recent form format
                    recent_form_data = self._convert_to_recent_form(stats, player, position)

                    # Apply to player - THIS IS THE KEY INTEGRATION POINT
                    player._recent_performance = recent_form_data

                    enriched_count += 1

                    if i < 10:
                        mult = recent_form_data.get('form_multiplier', 1.0)
                        trend = recent_form_data.get('trend', 'stable')
                        print(f"✅ {mult:.3f}x ({trend})")
                else:
                    if i < 10:
                        print("⚠️ No data")

            except Exception as e:
                if i < 10:
                    print(f"❌ Error: {e}")
                logger.error(f"Error enriching {player.name}: {e}")

        print(f"\n✅ Enriched {enriched_count}/{len(players)} players with recent form")
        return enriched_count

    def _convert_to_recent_form(self, stats: Dict, player, position: str) -> Dict:
        """
        Convert Statcast stats to the format expected by UnifiedScoringEngine

        Your system expects _recent_performance with:
        - form_multiplier (or form_score)
        - trend
        - other optional fields
        """
        # Default values
        form_multiplier = 1.0
        trend = "stable"
        hot_streak = False

        if position == "P":
            # Pitcher form based on xwOBA against
            xwoba = stats.get('xwOBA', 0.315)

            # Lower is better for pitchers
            if xwoba < 0.280:  # Elite
                form_multiplier = 1.15
                trend = "hot"
                hot_streak = True
            elif xwoba < 0.300:  # Very good
                form_multiplier = 1.08
                trend = "warm"
            elif xwoba > 0.350:  # Struggling
                form_multiplier = 0.92
                trend = "cold"
            elif xwoba > 0.330:  # Below average
                form_multiplier = 0.96
                trend = "cool"
            else:
                form_multiplier = 1.02
                trend = "stable"

        else:  # Hitter
            # Hitter form based on xwOBA
            xwoba = stats.get('xwOBA', 0.320)

            # Higher is better for hitters
            if xwoba > 0.380:  # Elite
                form_multiplier = 1.15
                trend = "hot"
                hot_streak = True
            elif xwoba > 0.350:  # Very good
                form_multiplier = 1.08
                trend = "warm"
            elif xwoba < 0.280:  # Struggling
                form_multiplier = 0.92
                trend = "cold"
            elif xwoba < 0.300:  # Below average
                form_multiplier = 0.96
                trend = "cool"
            else:
                form_multiplier = 1.02
                trend = "stable"

        # Also factor in hard hit rate if available
        hard_hit = stats.get('Hard_Hit', 0)
        if position != "P":  # For hitters
            if hard_hit > 45:  # Exceptional hard hit rate
                form_multiplier *= 1.03
            elif hard_hit < 30:  # Poor hard hit rate
                form_multiplier *= 0.97

        # Build the data structure your system expects
        recent_performance = {
            # REQUIRED by your UnifiedScoringEngine
            'form_score': form_multiplier,  # Your system looks for this
            'form_multiplier': form_multiplier,  # Alternative name

            # Additional useful data
            'trend': trend,
            'hot_streak': hot_streak,
            'games_analyzed': self.days_back,

            # Statcast specific metrics
            'xwOBA': xwoba,
            'hard_hit_pct': hard_hit,
            'exit_velocity': stats.get('avg_exit_velocity', 88.0),

            # Metadata
            'source': 'statcast_recent',
            'last_updated': datetime.now().isoformat(),

            # For display in GUI
            'display_text': self._get_display_text(trend, xwoba, position)
        }

        return recent_performance

    def _get_display_text(self, trend: str, xwoba: float, position: str) -> str:
        """Create display text for GUI"""
        emoji_map = {
            'hot': '🔥',
            'warm': '📈',
            'stable': '➡️',
            'cool': '📉',
            'cold': '❄️'
        }

        emoji = emoji_map.get(trend, '➡️')

        if position == "P":
            return f"{emoji} {trend.upper()} (xwOBA against: {xwoba:.3f})"
        else:
            return f"{emoji} {trend.upper()} (xwOBA: {xwoba:.3f})"


# Integration helper for your system
class StatcastRecentFormIntegration:
    """
    Helper class to integrate with your existing system
    """

    @staticmethod
    def apply_to_core(core):
        """
        Apply Statcast recent form to your BulletproofDFSCore

        Usage:
            StatcastRecentFormIntegration.apply_to_core(core)
        """
        if not hasattr(core, 'statcast_fetcher') or not core.statcast_fetcher:
            print("❌ Core doesn't have Statcast fetcher")
            return False

        # Create recent form enricher
        recent_form = IntegratedStatcastRecentForm(
            statcast_fetcher=core.statcast_fetcher,
            days_back=7
        )

        # Get eligible players
        eligible_players = core.get_eligible_players_by_mode()

        if not eligible_players:
            print("❌ No eligible players found")
            return False

        # Enrich players
        enriched = recent_form.enrich_players_with_recent_form(eligible_players)

        if enriched > 0:
            print(f"\n✅ Successfully enriched {enriched} players")
            print("📊 Your unified scoring engine will now use this data automatically!")
            return True

        return False

    @staticmethod
    def verify_integration(core):
        """
        Verify that recent form is properly integrated
        """
        print("\n🔍 VERIFYING STATCAST RECENT FORM INTEGRATION")
        print("=" * 60)

        # Check a few players
        sample_players = core.get_eligible_players_by_mode()[:5]

        for player in sample_players:
            print(f"\n{player.name}:")

            # Check if has recent performance
            if hasattr(player, '_recent_performance') and player._recent_performance:
                perf = player._recent_performance
                print(f"  ✅ Has recent performance data")
                print(f"  📊 Form multiplier: {perf.get('form_multiplier', 'N/A')}")
                print(f"  📈 Trend: {perf.get('trend', 'N/A')}")
                print(f"  🎯 Source: {perf.get('source', 'unknown')}")

                # Check if integrated with scoring
                if hasattr(player, 'enhanced_score'):
                    base = player.base_projection
                    enhanced = player.enhanced_score
                    if enhanced != base:
                        improvement = ((enhanced / base) - 1) * 100
                        print(f"  💰 Score impact: {base:.1f} → {enhanced:.1f} ({improvement:+.1f}%)")
                    else:
                        print(f"  ⚠️ No score enhancement yet")
            else:
                print(f"  ❌ No recent performance data")


# For GUI Integration
def add_to_gui_optimization(core):
    """
    This is called when user clicks "Optimize" in GUI
    Ensures recent form is applied before optimization
    """
    # Apply recent form if not already done
    if not hasattr(core, '_recent_form_applied'):
        print("📊 Applying Statcast recent form enrichment...")
        StatcastRecentFormIntegration.apply_to_core(core)
        core._recent_form_applied = True

    # Continue with normal optimization
    # Your existing optimization code runs here


if __name__ == "__main__":
    # Example usage
    print("""
    INTEGRATION INSTRUCTIONS:
    ========================

    1. In your BulletproofDFSCore or GUI optimization method, add:

       from integrated_statcast_recent_form import StatcastRecentFormIntegration

       # Before optimizing
       StatcastRecentFormIntegration.apply_to_core(core)

    2. Your unified scoring engine will automatically use the data!
       It looks for player._recent_performance['form_score']

    3. No changes needed to scoring engine - it already handles this!

    The integration is seamless because:
    - Sets _recent_performance attribute (what your system expects)
    - Provides form_score/form_multiplier (what scoring engine uses)
    - No competing calculations
    - Works with existing Statcast fetcher
    - Integrates with GUI optimization flow
    """)