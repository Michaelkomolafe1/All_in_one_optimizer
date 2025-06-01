#!/usr/bin/env python3
"""
Complete Baseball Savant Integration
Provides real Statcast data for DFS optimization
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Try to import pybaseball for real data
try:
    import pybaseball
    pybaseball.cache.enable()
    PYBASEBALL_AVAILABLE = True
    print("✅ PyBaseball available - Real Baseball Savant data enabled")
except ImportError:
    PYBASEBALL_AVAILABLE = False
    print("⚠️ PyBaseball not available - Install with: pip install pybaseball")

# Import simple fetcher as fallback
try:
    from simple_statcast_fetcher import SimpleStatcastFetcher
    SIMPLE_FETCHER_AVAILABLE = True
except ImportError:
    SIMPLE_FETCHER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatcastIntegration:
    """Complete Baseball Savant integration with multiple data sources"""

    def __init__(self):
        self.use_real_data = PYBASEBALL_AVAILABLE
        self.use_simple_fetcher = SIMPLE_FETCHER_AVAILABLE

        # Initialize data sources
        if self.use_simple_fetcher:
            self.simple_fetcher = SimpleStatcastFetcher()

        # Season dates (adjust as needed)
        self.season_start = '2024-03-28'
        self.season_end = '2024-09-29'

        print(f"🌐 StatcastIntegration initialized:")
        print(f"   PyBaseball: {'✅' if self.use_real_data else '❌'}")
        print(f"   Simple Fetcher: {'✅' if self.use_simple_fetcher else '❌'}")

    def enrich_player_data(self, players, force_refresh=False):
        """Enrich players with real Statcast data"""

        print(f"🔬 Enriching {len(players)} players with Baseball Savant data...")

        enhanced_players = []

        for player in players:
            try:
                player_name = getattr(player, 'name', '')
                position = getattr(player, 'primary_position', '')

                if not player_name or not position:
                    enhanced_players.append(player)
                    continue

                # Try to get real Statcast data
                statcast_data = self._fetch_player_statcast_data(player_name, position)

                if statcast_data:
                    # Apply real data to player
                    if hasattr(player, 'statcast_data'):
                        player.statcast_data = statcast_data

                    # Recalculate enhanced score if method exists
                    if hasattr(player, '_calculate_enhanced_score'):
                        player._calculate_enhanced_score()

                    print(f"✅ Real data: {player_name}")
                else:
                    # Use enhanced simulation as fallback
                    simulated_data = self._generate_enhanced_simulation(player)
                    if hasattr(player, 'statcast_data'):
                        player.statcast_data = simulated_data

                    if hasattr(player, '_calculate_enhanced_score'):
                        player._calculate_enhanced_score()

                    print(f"⚡ Simulation: {player_name}")

                enhanced_players.append(player)

            except Exception as e:
                logger.warning(f"Error enriching {player_name}: {e}")
                enhanced_players.append(player)
                continue

        # Stats summary
        real_data_count = sum(1 for p in enhanced_players 
                             if hasattr(p, 'statcast_data') and p.statcast_data and 
                             'Baseball Savant' in str(p.statcast_data.get('data_source', '')))

        print(f"📊 Enrichment Results:")
        print(f"   Real Baseball Savant data: {real_data_count} players")
        print(f"   Enhanced simulation: {len(enhanced_players) - real_data_count} players")

        return enhanced_players

    def _fetch_player_statcast_data(self, player_name: str, position: str) -> Optional[Dict]:
        """Fetch real Statcast data for a player"""

        # Method 1: Use simple fetcher if available
        if self.use_simple_fetcher:
            try:
                data = self.simple_fetcher.fetch_player_data(player_name, position)
                if data:
                    return data
            except Exception as e:
                logger.debug(f"Simple fetcher failed for {player_name}: {e}")

        # Method 2: Use pybaseball directly if available
        if self.use_real_data:
            try:
                return self._fetch_with_pybaseball(player_name, position)
            except Exception as e:
                logger.debug(f"PyBaseball failed for {player_name}: {e}")

        # Method 3: Return None to trigger simulation
        return None

    def _fetch_with_pybaseball(self, player_name: str, position: str) -> Optional[Dict]:
        """Fetch data using pybaseball directly"""

        if not PYBASEBALL_AVAILABLE:
            return None

        try:
            # Get player ID
            name_parts = player_name.strip().split()
            if len(name_parts) < 2:
                return None

            first_name = name_parts[0]
            last_name = name_parts[-1]

            lookup = pybaseball.playerid_lookup(last_name, first_name)

            if len(lookup) == 0:
                return None

            player_id = int(lookup.iloc[0]['key_mlbam'])

            # Fetch Statcast data
            if position == 'P':
                data = pybaseball.statcast_pitcher(
                    start_dt=self.season_start,
                    end_dt=self.season_end,
                    player_id=player_id
                )
            else:
                data = pybaseball.statcast_batter(
                    start_dt=self.season_start,
                    end_dt=self.season_end,
                    player_id=player_id
                )

            if data is None or len(data) == 0:
                return None

            # Process data into metrics
            if position == 'P':
                metrics = {
                    'xwOBA': self._safe_mean(data, 'estimated_woba_using_speedangle', 0.310),
                    'Hard_Hit': self._safe_percentage(data, 'launch_speed', lambda x: x >= 95, 33.0),
                    'K': self._safe_event_rate(data, 'strikeout', 20.0),
                    'data_source': 'Baseball Savant (PyBaseball)',
                    'player_id': player_id,
                    'player_name': player_name,
                    'last_updated': datetime.now().isoformat()
                }
            else:
                metrics = {
                    'xwOBA': self._safe_mean(data, 'estimated_woba_using_speedangle', 0.320),
                    'Hard_Hit': self._safe_percentage(data, 'launch_speed', lambda x: x >= 95, 35.0),
                    'Barrel': self._safe_barrel_rate(data),
                    'data_source': 'Baseball Savant (PyBaseball)',
                    'player_id': player_id,
                    'player_name': player_name,
                    'last_updated': datetime.now().isoformat()
                }

            return metrics

        except Exception as e:
            logger.debug(f"PyBaseball fetch failed for {player_name}: {e}")
            return None

    def _safe_mean(self, data: pd.DataFrame, column: str, default: float) -> float:
        """Safely calculate mean of a column"""
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    return float(series.mean())
        except:
            pass
        return default

    def _safe_percentage(self, data: pd.DataFrame, column: str, condition_func, default: float) -> float:
        """Safely calculate percentage based on condition"""
        try:
            if column in data.columns:
                series = data[column].dropna()
                if len(series) > 0:
                    meeting_condition = condition_func(series).sum()
                    return float(meeting_condition / len(series) * 100)
        except:
            pass
        return default

    def _safe_barrel_rate(self, data: pd.DataFrame) -> float:
        """Safely calculate barrel rate"""
        try:
            barrel_columns = ['barrel', 'is_barrel', 'barrels']
            for col in barrel_columns:
                if col in data.columns:
                    barrel_data = data[col].dropna()
                    if len(barrel_data) > 0:
                        if barrel_data.dtype == 'bool':
                            return float(barrel_data.sum() / len(data) * 100)
                        else:
                            return float(barrel_data.mean() * 100)
        except:
            pass
        return 6.0

    def _safe_event_rate(self, data: pd.DataFrame, event_type: str, default: float) -> float:
        """Safely calculate event rate"""
        try:
            if 'events' in data.columns:
                events = data['events'].dropna()
                if len(events) > 0:
                    event_count = (events == event_type).sum()
                    return float(event_count / len(events) * 100)
        except:
            pass
        return default

    def _generate_enhanced_simulation(self, player) -> Dict:
        """Generate enhanced simulation data for players without real data"""

        player_name = getattr(player, 'name', 'Unknown')
        position = getattr(player, 'primary_position', 'UTIL')
        salary = getattr(player, 'salary', 3000)

        # Use player name for consistent randomization
        np.random.seed(hash(player_name) % 1000000)

        # Salary-based factor (higher salary = better stats)
        if position == 'P':
            salary_factor = min(salary / 10000.0, 1.2)
            simulated_data = {
                'xwOBA': round(max(0.250, np.random.normal(0.310 - (salary_factor * 0.020), 0.030)), 3),
                'Hard_Hit': round(max(0, np.random.normal(35.0 - (salary_factor * 3.0), 5.0)), 1),
                'K': round(max(0, np.random.normal(20.0 + (salary_factor * 5.0), 4.0)), 1),
                'data_source': 'Enhanced Simulation'
            }
        else:
            salary_factor = min(salary / 5000.0, 1.2)
            simulated_data = {
                'xwOBA': round(max(0.250, np.random.normal(0.310 + (salary_factor * 0.030), 0.040)), 3),
                'Hard_Hit': round(max(0, np.random.normal(30.0 + (salary_factor * 8.0), 7.0)), 1),
                'Barrel': round(max(0, np.random.normal(5.0 + (salary_factor * 4.0), 3.0)), 1),
                'data_source': 'Enhanced Simulation'
            }

        return simulated_data


# Test function
def test_statcast_integration():
    """Test the Statcast integration"""
    print("🧪 Testing Statcast Integration...")

    integration = StatcastIntegration()

    # Mock player for testing
    class MockPlayer:
        def __init__(self, name, position, salary):
            self.name = name
            self.primary_position = position
            self.salary = salary
            self.statcast_data = {}

        def _calculate_enhanced_score(self):
            pass

    # Test with a known player
    test_players = [
        MockPlayer("Aaron Judge", "OF", 5000),
        MockPlayer("Gerrit Cole", "P", 9000)
    ]

    enhanced = integration.enrich_player_data(test_players)

    for player in enhanced:
        if hasattr(player, 'statcast_data') and player.statcast_data:
            print(f"✅ {player.name}: {player.statcast_data.get('data_source', 'Unknown')}")
        else:
            print(f"❌ {player.name}: No data")

    print("✅ Statcast integration test complete!")


if __name__ == "__main__":
    test_statcast_integration()
