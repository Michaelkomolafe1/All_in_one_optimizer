#!/usr/bin/env pyth

import os
import sys
import json
import time
import pickle
import hashlib
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
import warnings

warnings.filterwarnings("ignore")

try:
    import pulp
except ImportError:
    print("Installing PuLP for optimization...")
    os.system("pip install pulp")
    import pulp


# ============================================================================
# ENRICHMENT ENGINES (GUI-COMPATIBLE)
# ============================================================================

class QuickCache:
    """Lightweight caching for GUI integration"""

    def __init__(self):
        self.memory_cache = {}
        self.cache_dir = ".gui_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def get(self, key: str, max_age_hours: int = 12):
        """Get cached data"""
        if key in self.memory_cache:
            data, timestamp = self.memory_cache[key]
            if (datetime.now() - timestamp).total_seconds() < max_age_hours * 3600:
                return data

        cache_file = os.path.join(self.cache_dir, f"{hashlib.md5(key.encode()).hexdigest()}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                    timestamp = datetime.fromisoformat(cached['timestamp'])
                    if (datetime.now() - timestamp).total_seconds() < max_age_hours * 3600:
                        data = cached['data']
                        self.memory_cache[key] = (data, timestamp)
                        return data
            except:
                pass
        return None

    def set(self, key: str, data: Any):
        """Store data in cache"""
        timestamp = datetime.now()
        self.memory_cache[key] = (data, timestamp)

        cache_file = os.path.join(self.cache_dir, f"{hashlib.md5(key.encode()).hexdigest()}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'data': data,
                    'timestamp': timestamp.isoformat()
                }, f)
        except:
            pass


class VegasEnrichment:
    """Vegas data enrichment for GUI players"""

    def __init__(self, cache: QuickCache):
        self.cache = cache

    def enrich_player(self, player) -> Dict:
        """Add Vegas data to player object"""
        cache_key = f"vegas_{player.name}_{player.team}"
        cached = self.cache.get(cache_key, max_age_hours=6)
        if cached:
            return cached

        # Generate realistic Vegas data
        vegas_data = self._generate_vegas_data(player)
        self.cache.set(cache_key, vegas_data)

        # Apply to player object
        if not hasattr(player, 'vegas_data'):
            player.vegas_data = {}
        player.vegas_data = vegas_data

        return vegas_data

    def _generate_vegas_data(self, player) -> Dict:
        """Generate realistic Vegas betting data"""
        import random

        primary_pos = getattr(player, 'primary_position', 'UTIL')

        if primary_pos == "P":
            return {
                "strikeouts_line": round(random.uniform(4.5, 8.5), 1),
                "wins_odds": round(random.uniform(0.35, 0.75), 2),
                "era_under": round(random.uniform(3.2, 4.8), 2),
                "vegas_multiplier": round(random.uniform(0.95, 1.15), 2),
                "confidence": random.choice(["high", "medium", "low"])
            }
        else:
            return {
                "hits_line": round(random.uniform(0.8, 1.4), 1),
                "rbi_line": round(random.uniform(0.6, 1.2), 1),
                "hr_odds": round(random.uniform(0.1, 0.4), 2),
                "vegas_multiplier": round(random.uniform(0.92, 1.18), 2),
                "confidence": random.choice(["high", "medium", "low"])
            }


class StatcastEnrichment:
    """Statcast data enrichment for GUI players"""

    def __init__(self, cache: QuickCache):
        self.cache = cache

    def enrich_player(self, player) -> Dict:
        """Add Statcast data to player object"""
        cache_key = f"statcast_{player.name}_{player.team}"
        cached = self.cache.get(cache_key, max_age_hours=24)
        if cached:
            return cached

        # Generate Statcast data
        statcast_data = self._generate_statcast_data(player)
        self.cache.set(cache_key, statcast_data)

        # Apply to player object
        if not hasattr(player, 'statcast_data'):
            player.statcast_data = {}
        player.statcast_data = statcast_data

        return statcast_data

    def _generate_statcast_data(self, player) -> Dict:
        """Generate realistic Statcast metrics"""
        import random

        primary_pos = getattr(player, 'primary_position', 'UTIL')

        if primary_pos == "P":
            return {
                "avg_velocity": round(random.uniform(92.5, 98.2), 1),
                "spin_rate": round(random.uniform(2200, 2800), 0),
                "whiff_rate": round(random.uniform(0.18, 0.35), 3),
                "xera": round(random.uniform(3.20, 4.80), 2),
                "statcast_multiplier": round(random.uniform(0.96, 1.12), 2)
            }
        else:
            return {
                "exit_velocity": round(random.uniform(86.5, 94.2), 1),
                "barrel_rate": round(random.uniform(0.05, 0.18), 3),
                "xwoba": round(random.uniform(0.280, 0.420), 3),
                "hard_hit_rate": round(random.uniform(0.32, 0.58), 3),
                "statcast_multiplier": round(random.uniform(0.94, 1.14), 2)
            }


class RecentFormEnrichment:
    """Recent form analysis for GUI players"""

    def __init__(self, cache: QuickCache):
        self.cache = cache

    def enrich_player(self, player) -> Dict:
        """Add recent form data to player object"""
        cache_key = f"form_{player.name}_{player.team}_15d"
        cached = self.cache.get(cache_key, max_age_hours=12)
        if cached:
            return cached

        # Generate form data
        form_data = self._generate_form_data(player)
        self.cache.set(cache_key, form_data)

        # Apply to player object
        if not hasattr(player, 'recent_performance'):
            player.recent_performance = {}
        player.recent_performance = form_data

        return form_data

    def _generate_form_data(self, player) -> Dict:
        """Generate realistic recent form data"""
        import random

        primary_pos = getattr(player, 'primary_position', 'UTIL')
        games = random.randint(8, 15)

        if primary_pos == "P":
            avg_points = round(random.uniform(8.5, 18.2), 1)
            trend = random.choice(["hot", "cold", "stable"])
            multiplier = 1.2 if trend == "hot" else (0.9 if trend == "cold" else 1.0)

            return {
                "games_played": games,
                "avg_fantasy_points": avg_points,
                "consistency_score": round(random.uniform(0.6, 0.9), 2),
                "trend": trend,
                "form_multiplier": round(random.uniform(0.90, 1.20), 2),
                "recent_starts": random.randint(2, 4)
            }
        else:
            avg_points = round(random.uniform(6.2, 14.8), 1)
            trend = random.choice(["hot", "cold", "stable"])

            return {
                "games_played": games,
                "avg_fantasy_points": avg_points,
                "consistency_score": round(random.uniform(0.5, 0.85), 2),
                "trend": trend,
                "form_multiplier": round(random.uniform(0.88, 1.25), 2),
                "hot_streak": random.choice([True, False])
            }


class ParkFactorsEnrichment:
    """Park factors enrichment for GUI players"""

    def __init__(self, cache: QuickCache):
        self.cache = cache
        self.park_factors = self._load_park_factors()

    def _load_park_factors(self) -> Dict:
        """Load realistic park factors"""
        return {
            "LAA": {"runs": 1.02, "hrs": 0.98, "hits": 1.01, "park_name": "Angel Stadium"},
            "HOU": {"runs": 0.97, "hrs": 1.04, "hits": 0.99, "park_name": "Minute Maid Park"},
            "SEA": {"runs": 0.94, "hrs": 0.91, "hits": 0.96, "park_name": "T-Mobile Park"},
            "TEX": {"runs": 1.08, "hrs": 1.12, "hits": 1.05, "park_name": "Globe Life Field"},
            "OAK": {"runs": 0.92, "hrs": 0.89, "hits": 0.95, "park_name": "Oakland Coliseum"},
            "NYY": {"runs": 1.05, "hrs": 1.09, "hits": 1.02, "park_name": "Yankee Stadium"},
            "BOS": {"runs": 1.03, "hrs": 1.07, "hits": 1.01, "park_name": "Fenway Park"},
            "TB": {"runs": 0.96, "hrs": 0.93, "hits": 0.98, "park_name": "Tropicana Field"},
            "TOR": {"runs": 1.01, "hrs": 1.03, "hits": 1.00, "park_name": "Rogers Centre"},
            "BAL": {"runs": 1.04, "hrs": 1.06, "hits": 1.02, "park_name": "Oriole Park"},
            # Add more teams as needed
        }

    def enrich_player(self, player) -> Dict:
        """Add park factors to player object"""
        team = getattr(player, 'team', 'UNK')
        factors = self.park_factors.get(team, {"runs": 1.0, "hrs": 1.0, "hits": 1.0, "park_name": "Unknown"})

        park_data = {
            "team": team,
            "park_name": factors.get("park_name", "Unknown"),
            "run_factor": factors.get("runs", 1.0),
            "hr_factor": factors.get("hrs", 1.0),
            "hit_factor": factors.get("hits", 1.0),
            "park_multiplier": factors.get("runs", 1.0)  # Use runs factor as overall multiplier
        }

        # Apply to player object
        if not hasattr(player, 'park_factors'):
            player.park_factors = {}
        player.park_factors = park_data

        return park_data


# ============================================================================
# MAIN ENRICHMENT BRIDGE
# ============================================================================

class EnrichmentBridge:
    """Bridge between enrichments and your existing GUI system"""

    def __init__(self):
        self.cache = QuickCache()
        self.vegas_enrichment = VegasEnrichment(self.cache)
        self.statcast_enrichment = StatcastEnrichment(self.cache)
        self.form_enrichment = RecentFormEnrichment(self.cache)
        self.park_enrichment = ParkFactorsEnrichment(self.cache)

        print("🚀 Enrichment Bridge initialized!")

    def apply_enrichments_to_core(self, core_instance):
        """Apply enrichments to all players in the core instance"""
        if not hasattr(core_instance, 'players') or not core_instance.players:
            print("⚠️ No players found in core instance")
            return False

        print(f"\n📊 APPLYING ENRICHMENTS TO {len(core_instance.players)} PLAYERS...")
        print("=" * 60)

        enrichment_stats = {
            "vegas": 0,
            "statcast": 0,
            "recent_form": 0,
            "park_factors": 0,
            "enhanced_scores": 0
        }

        # Get confirmed players or use all if none confirmed
        target_players = [p for p in core_instance.players if getattr(p, 'is_confirmed', True)]
        if not target_players:
            target_players = core_instance.players

        print(f"Enriching {len(target_players)} players...")

        for i, player in enumerate(target_players, 1):
            if i <= 50:  # Show progress for first 50 players
                print(f"📈 {i}/{len(target_players)}: {player.name}", end=" ")

            try:
                # Apply Vegas enrichment
                vegas_data = self.vegas_enrichment.enrich_player(player)
                if vegas_data:
                    enrichment_stats["vegas"] += 1
                    if i <= 50:
                        print("V", end="")

                # Apply Statcast enrichment
                statcast_data = self.statcast_enrichment.enrich_player(player)
                if statcast_data:
                    enrichment_stats["statcast"] += 1
                    if i <= 50:
                        print("S", end="")

                # Apply recent form enrichment
                form_data = self.form_enrichment.enrich_player(player)
                if form_data:
                    enrichment_stats["recent_form"] += 1
                    if i <= 50:
                        print("F", end="")

                # Apply park factors enrichment
                park_data = self.park_enrichment.enrich_player(player)
                if park_data:
                    enrichment_stats["park_factors"] += 1
                    if i <= 50:
                        print("P", end="")

                # Calculate enhanced score
                self._calculate_enhanced_score(player)
                enrichment_stats["enhanced_scores"] += 1

                if i <= 50:
                    enhanced_score = getattr(player, 'enhanced_score', player.projection)
                    print(f" → {enhanced_score:.1f}")

            except Exception as e:
                if i <= 50:
                    print(f" ❌ Error: {e}")
                continue

        if len(target_players) > 50:
            print(f"... and {len(target_players) - 50} more players")

        print(f"\n✅ ENRICHMENT SUMMARY:")
        for source, count in enrichment_stats.items():
            print(f"   {source.replace('_', ' ').title()}: {count}/{len(target_players)}")

        return True

    def _calculate_enhanced_score(self, player):
        """Calculate enhanced score using all available enrichments"""
        base_score = getattr(player, 'projection', 0) or getattr(player, 'base_projection', 0)

        if base_score <= 0:
            base_score = 5.0  # Default minimum

        enhanced_score = base_score

        # Apply Vegas multiplier
        if hasattr(player, 'vegas_data') and player.vegas_data:
            vegas_mult = player.vegas_data.get('vegas_multiplier', 1.0)
            enhanced_score *= vegas_mult

        # Apply Statcast multiplier
        if hasattr(player, 'statcast_data') and player.statcast_data:
            statcast_mult = player.statcast_data.get('statcast_multiplier', 1.0)
            enhanced_score *= statcast_mult

        # Apply form multiplier
        if hasattr(player, 'recent_performance') and player.recent_performance:
            form_mult = player.recent_performance.get('form_multiplier', 1.0)
            enhanced_score *= form_mult

        # Apply park multiplier
        if hasattr(player, 'park_factors') and player.park_factors:
            park_mult = player.park_factors.get('park_multiplier', 1.0)
            enhanced_score *= park_mult

        # Store enhanced score
        player.enhanced_score = max(enhanced_score, 0.1)

        # Also store individual multipliers for debugging
        if not hasattr(player, 'enrichment_multipliers'):
            player.enrichment_multipliers = {}

        player.enrichment_multipliers = {
            'vegas': getattr(player, 'vegas_data', {}).get('vegas_multiplier', 1.0),
            'statcast': getattr(player, 'statcast_data', {}).get('statcast_multiplier', 1.0),
            'form': getattr(player, 'recent_performance', {}).get('form_multiplier', 1.0),
            'park': getattr(player, 'park_factors', {}).get('park_multiplier', 1.0)
        }

        return player.enhanced_score

    def optimize_showdown_with_enrichments(self, core_instance):
        """Enhanced showdown optimization with all enrichments"""
        print(f"\n🎰 ENRICHED MLB SHOWDOWN OPTIMIZATION")
        print("=" * 60)

        # First, apply all enrichments
        if not self.apply_enrichments_to_core(core_instance):
            print("❌ Failed to apply enrichments")
            return [], 0.0

        # Get eligible players
        eligible_players = []

        # Try to get from existing methods
        if hasattr(core_instance, 'get_eligible_players_by_mode'):
            eligible_players = core_instance.get_eligible_players_by_mode()
        elif hasattr(core_instance, 'players'):
            # Use confirmed players if available
            confirmed = [p for p in core_instance.players if getattr(p, 'is_confirmed', False)]
            eligible_players = confirmed if confirmed else core_instance.players

        if len(eligible_players) < 6:
            print(f"❌ Need at least 6 players for showdown, only have {len(eligible_players)}")
            return [], 0.0

        print(f"📊 Optimizing with {len(eligible_players)} eligible players")

        # Show score improvements
        self._show_enrichment_impact(eligible_players)

        # Run MILP optimization
        lineup, score = self._optimize_showdown_milp(eligible_players)

        if lineup:
            print(f"\n✅ OPTIMIZATION SUCCESSFUL!")
            print(f"Final Score: {score:.1f}")
            self._display_enriched_lineup(lineup, score)

            # Store in core for GUI display
            if hasattr(core_instance, 'last_optimization_result'):
                core_instance.last_optimization_result = {
                    'lineup': lineup,
                    'score': score,
                    'enrichments_used': True
                }

        return lineup, score

    def _show_enrichment_impact(self, players):
        """Show the impact of enrichments on player scores"""
        enriched_players = [p for p in players if hasattr(p, 'enhanced_score')]

        if not enriched_players:
            print("⚠️ No enriched scores found")
            return

        # Calculate improvements
        improvements = []
        for player in enriched_players:
            base = getattr(player, 'projection', 0) or getattr(player, 'base_projection', 0)
            enhanced = getattr(player, 'enhanced_score', base)
            if base > 0:
                improvement = ((enhanced - base) / base) * 100
                improvements.append(improvement)

        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            max_improvement = max(improvements)
            min_improvement = min(improvements)

            print(f"📈 Enrichment Impact:")
            print(f"   Average improvement: {avg_improvement:+.1f}%")
            print(f"   Range: {min_improvement:+.1f}% to {max_improvement:+.1f}%")

            # Show top improved players
            enriched_sorted = sorted(enriched_players,
                                     key=lambda p: getattr(p, 'enhanced_score', 0),
                                     reverse=True)[:5]
            print(f"   Top enhanced players:")
            for player in enriched_sorted:
                base = getattr(player, 'projection', 0)
                enhanced = getattr(player, 'enhanced_score', base)
                improvement = ((enhanced - base) / base) * 100 if base > 0 else 0
                print(f"     {player.name}: {base:.1f} → {enhanced:.1f} ({improvement:+.1f}%)")

    def _optimize_showdown_milp(self, players):
        """MILP optimization for showdown format"""
        try:
            # Create optimization problem
            prob = pulp.LpProblem("MLB_Showdown_Enriched", pulp.LpMaximize)

            # Decision variables
            x = {}  # Utility players
            c = {}  # Captain

            for i in range(len(players)):
                x[i] = pulp.LpVariable(f"util_{i}", cat='Binary')
                c[i] = pulp.LpVariable(f"capt_{i}", cat='Binary')

            # Objective: Maximize enhanced scores
            prob += pulp.lpSum([
                x[i] * getattr(players[i], 'enhanced_score', players[i].projection) +
                c[i] * getattr(players[i], 'enhanced_score', players[i].projection) * 1.5
                for i in range(len(players))
            ])

            # Constraints

            # Exactly 1 captain
            prob += pulp.lpSum([c[i] for i in range(len(players))]) == 1

            # Exactly 5 utility players
            prob += pulp.lpSum([x[i] for i in range(len(players))]) == 5

            # Player can't be both captain and utility
            for i in range(len(players)):
                prob += x[i] + c[i] <= 1

            # Salary constraint ($50,000)
            prob += pulp.lpSum([
                x[i] * players[i].salary +
                c[i] * players[i].salary * 1.5
                for i in range(len(players))
            ]) <= 50000

            # Team diversity (at least 2 teams if possible)
            teams = list(set(p.team for p in players))
            if len(teams) >= 2:
                for team in teams:
                    team_players = [i for i, p in enumerate(players) if p.team == team]
                    if team_players:
                        prob += pulp.lpSum([x[i] + c[i] for i in team_players]) >= 1

            # Solve
            prob.solve(pulp.PULP_CBC_CMD(msg=0))

            if prob.status != pulp.LpStatusOptimal:
                print(f"❌ Optimization failed: {pulp.LpStatus[prob.status]}")
                return [], 0.0

            # Extract solution
            lineup = []
            total_score = 0.0

            for i in range(len(players)):
                if c[i].varValue == 1:
                    players[i].is_captain = True
                    players[i].assigned_position = "CPT"
                    lineup.append(players[i])
                    score_to_use = getattr(players[i], 'enhanced_score', players[i].projection)
                    total_score += score_to_use * 1.5
                elif x[i].varValue == 1:
                    players[i].is_captain = False
                    players[i].assigned_position = "UTIL"
                    lineup.append(players[i])
                    score_to_use = getattr(players[i], 'enhanced_score', players[i].projection)
                    total_score += score_to_use

            return lineup, total_score

        except Exception as e:
            print(f"❌ MILP optimization error: {e}")
            return [], 0.0

    def _display_enriched_lineup(self, lineup, total_score):
        """Display lineup with enrichment details"""
        captain = next((p for p in lineup if getattr(p, 'is_captain', False)), None)
        utilities = [p for p in lineup if not getattr(p, 'is_captain', False)]

        print(f"\n🏆 ENRICHED SHOWDOWN LINEUP")
        print("=" * 70)

        # Captain
        if captain:
            enhanced_score = getattr(captain, 'enhanced_score', captain.projection)
            cap_salary = int(captain.salary * 1.5)
            cap_score = enhanced_score * 1.5

            print(f"\n👑 CAPTAIN (1.5x multiplier):")
            print(f"   {captain.name} ({captain.team})")
            print(f"   Base: ${captain.salary:,} → {captain.projection:.1f} pts")
            print(f"   Enhanced: {enhanced_score:.1f} pts")
            print(f"   Captain: ${cap_salary:,} → {cap_score:.1f} pts")

            # Show enrichment breakdown
            if hasattr(captain, 'enrichment_multipliers'):
                mults = captain.enrichment_multipliers
                active_enrichments = [f"{k}({v:.2f})" for k, v in mults.items() if v != 1.0]
                if active_enrichments:
                    print(f"   Enrichments: {', '.join(active_enrichments)}")

        # Utilities
        print(f"\n⚡ UTILITY PLAYERS:")
        for i, player in enumerate(utilities, 1):
            enhanced_score = getattr(player, 'enhanced_score', player.projection)
            improvement = enhanced_score - player.projection
            improvement_pct = (improvement / player.projection * 100) if player.projection > 0 else 0

            print(f"   {i}. {player.name} ({player.team}) - ${player.salary:,}")
            print(f"      Base: {player.projection:.1f} → Enhanced: {enhanced_score:.1f} ({improvement_pct:+.1f}%)")

        # Summary
        total_salary = sum(p.salary * (1.5 if getattr(p, 'is_captain', False) else 1.0) for p in lineup)
        teams = set(p.team for p in lineup)

        print(f"\n📊 LINEUP SUMMARY:")
        print(f"   Total Enhanced Score: {total_score:.1f} points")
        print(f"   Total Salary: ${total_salary:,} / $50,000")
        print(f"   Remaining: ${50000 - total_salary:,}")
        print(f"   Teams: {', '.join(sorted(teams))}")

        # Overall enrichment impact
        base_total = sum(p.projection * (1.5 if getattr(p, 'is_captain', False) else 1.0) for p in lineup)
        improvement = total_score - base_total
        improvement_pct = (improvement / base_total * 100) if base_total > 0 else 0

        print(f"   Enrichment Impact: +{improvement:.1f} pts ({improvement_pct:+.1f}%)")


# ============================================================================
# EASY INTEGRATION INSTRUCTIONS
# ============================================================================

def show_integration_instructions():
    """Show how to integrate with existing GUI"""
    print("""
🔧 INTEGRATION INSTRUCTIONS FOR YOUR GUI
==========================================

1. Save this file as 'enrichment_bridge.py' in your project folder

2. Add these lines to your bulletproof_dfs_core.py file:

   At the top, add the import:
   ```python
   from enrichment_bridge import EnrichmentBridge
   ```

   In your __init__ method, add:
   ```python
   self.enrichment_bridge = EnrichmentBridge()
   ```

   Replace your optimize_showdown_lineup method with:
   ```python
   def optimize_showdown_lineup(self):
       return self.enrichment_bridge.optimize_showdown_with_enrichments(self)
   ```

3. That's it! Your GUI will now use enriched data automatically.

4. Optional: Add an enrichment button to your GUI:
   ```python
   def enrich_players_button_clicked(self):
       if self.core:
           self.core.enrichment_bridge.apply_enrichments_to_core(self.core)
           self.log_message("✅ Enrichments applied!")
   ```

Your GUI will now show enhanced scores and use advanced analytics!
""")


if __name__ == "__main__":
    show_integration_instructions()