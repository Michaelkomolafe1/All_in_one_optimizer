#!/usr/bin/env python3
"""
Real Recent Form Analyzer - Uses actual game logs from Baseball Savant
"""

from pybaseball import statcast_batter, playerid_lookup
from datetime import datetime, timedelta
import pandas as pd
import time


class RealRecentFormAnalyzer:
    def __init__(self, days_back=7):
        self.days_back = days_back
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days_back)

    def get_player_game_logs(self, player_name):
        """Fetch real game logs for a player"""
        try:
            # Split name for lookup
            parts = player_name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = ' '.join(parts[1:])

                # Look up player ID
                player_data = playerid_lookup(last, first)
                if player_data.empty:
                    return None

                # Get the most recent player (active)
                player_id = int(player_data.iloc[0]['key_mlbam'])

                # Fetch recent game data
                data = statcast_batter(
                    start_dt=self.start_date.strftime('%Y-%m-%d'),
                    end_dt=self.end_date.strftime('%Y-%m-%d'),
                    player_id=player_id
                )

                return data

        except Exception as e:
            print(f"Could not fetch data for {player_name}: {e}")
            return None

    def calculate_form_metrics(self, game_data):
        """Calculate form rating from real game data"""
        if game_data is None or game_data.empty:
            return {
                'form_rating': 1.0,
                'hot_streak': False,
                'games_played': 0,
                'recent_avg': .250,
                'recent_ops': .700,
                'xba': .250
            }

        # Calculate real metrics
        games = len(game_data['game_date'].unique())
        hits = len(game_data[game_data['events'] == 'single']) + \
               len(game_data[game_data['events'] == 'double']) + \
               len(game_data[game_data['events'] == 'triple']) + \
               len(game_data[game_data['events'] == 'home_run'])
        at_bats = len(game_data[game_data['events'].notna()])

        # Recent batting average
        recent_avg = hits / at_bats if at_bats > 0 else .250

        # Expected batting average (if available)
        xba = game_data[
            'estimated_ba_using_speedangle'].mean() if 'estimated_ba_using_speedangle' in game_data.columns else recent_avg

        # Simple OPS calculation
        walks = len(game_data[game_data['events'] == 'walk'])
        obp = (hits + walks) / (at_bats + walks) if (at_bats + walks) > 0 else .300

        # Total bases for SLG
        singles = len(game_data[game_data['events'] == 'single'])
        doubles = len(game_data[game_data['events'] == 'double'])
        triples = len(game_data[game_data['events'] == 'triple'])
        homers = len(game_data[game_data['events'] == 'home_run'])
        total_bases = singles + (2 * doubles) + (3 * triples) + (4 * homers)
        slg = total_bases / at_bats if at_bats > 0 else .400

        recent_ops = obp + slg

        # Form rating based on performance vs league average
        form_rating = 1.0
        if recent_avg > .300:
            form_rating = 1.1 + ((recent_avg - .300) * 2)  # Boost for hot hitters
        elif recent_avg < .200:
            form_rating = 0.9 - ((0.200 - recent_avg) * 2)  # Penalty for cold hitters

        # Hot streak if hitting .350+ or 2+ homers in period
        hot_streak = recent_avg > .350 or homers >= 2

        return {
            'form_rating': min(max(form_rating, 0.7), 1.3),  # Cap between 0.7-1.3
            'hot_streak': hot_streak,
            'games_played': games,
            'recent_avg': recent_avg,
            'recent_ops': recent_ops,
            'xba': xba if pd.notna(xba) else recent_avg,
            'hits_last_x': hits,
            'homers_last_x': homers
        }

    def enrich_players_with_form(self, players):
        """Add real form data to players with progress tracking"""
        print(f"\n📊 Fetching real game logs for last {self.days_back} days...")

        # Import progress tracker if available
        try:
            from progress_tracker import ProgressTracker
            tracker = ProgressTracker(len(players), "Analyzing player form", show_eta=True)
        except:
            tracker = None

        successful_analyses = 0
        failed_analyses = 0

        for i, player in enumerate(players):
            try:
                # Update progress
                if tracker:
                    tracker.update(1, f"{player.name}")
                else:
                    # Fallback progress display
                    if (i + 1) % 5 == 0:
                        print(f"  Processing {i + 1}/{len(players)} players...")

                # Skip if player already has recent form data
                if hasattr(player, 'form_rating') and player.form_rating != 1.0:
                    continue

                # Fetch real game data
                game_data = self.get_player_game_logs(player.name)

                # Calculate form metrics
                metrics = self.calculate_form_metrics(game_data)

                # Apply to player
                player.form_rating = metrics['form_rating']
                player.hot_streak = metrics['hot_streak']
                player.recent_avg = metrics['recent_avg']
                player.recent_ops = metrics['recent_ops']

                # Add descriptive attributes
                if metrics['hot_streak']:
                    player.form_description = f"🔥 HOT: .{int(metrics['recent_avg'] * 1000)} last {self.days_back}d"
                elif metrics['form_rating'] < 0.9:
                    player.form_description = f"❄️ COLD: .{int(metrics['recent_avg'] * 1000)} last {self.days_back}d"
                else:
                    player.form_description = f"AVG: .{int(metrics['recent_avg'] * 1000)} last {self.days_back}d"

                # Track success
                if metrics['games_played'] > 0:
                    successful_analyses += 1
                else:
                    failed_analyses += 1

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                failed_analyses += 1
                if tracker is None:  # Only print errors if no progress tracker
                    print(f"⚠️ Error analyzing {player.name}: {e}")

        # Finish progress tracking
        if tracker:
            tracker.finish()

        print(f"✅ Form analysis complete: {successful_analyses} successful, {failed_analyses} failed")

        # Report hot/cold summary
        hot_count = sum(1 for p in players if hasattr(p, 'hot_streak') and p.hot_streak)
        cold_count = sum(1 for p in players if hasattr(p, 'form_rating') and p.form_rating < 0.9)

        if hot_count > 0:
            print(f"   🔥 {hot_count} HOT players identified")
        if cold_count > 0:
            print(f"   ❄️ {cold_count} COLD players identified")

        return successful_analyses