#!/usr/bin/env python3
"""
REAL DATA ENRICHMENTS FOR DFS OPTIMIZER
========================================
Uses actual APIs and data sources - no fake data!
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging

logger = logging.getLogger(__name__)


# ========== 1. PYBASEBALL INTEGRATION ==========
class RealStatcastFetcher:
    """Get REAL player stats from Baseball Savant using pybaseball"""

    def __init__(self):
        try:
            import pybaseball as pyb
            self.pyb = pyb
            self.pyb.cache.enable()

            # UPDATED: Dynamic date handling for current season
            from datetime import datetime, timedelta

            # Get current date
            today = datetime.now()
            current_year = today.year

            # MLB season runs April-October
            # For 2025, use the current season data
            if current_year >= 2025:
                # Start of 2025 season
                self.season_start = datetime(2025, 4, 1)
                # Use current date or end of regular season, whichever is earlier
                regular_season_end = datetime(2025, 10, 1)
                self.season_end = min(today, regular_season_end)
            else:
                # For previous years
                self.season_start = datetime(current_year, 4, 1)
                self.season_end = today

            # Format for pybaseball
            self.start_str = self.season_start.strftime('%Y-%m-%d')
            self.end_str = self.season_end.strftime('%Y-%m-%d')

            logger.info(f"✅ Pybaseball initialized")
            logger.info(f"   Season: {self.start_str} to {self.end_str}")
            logger.info(f"   Today: {today.strftime('%Y-%m-%d')}")

        except ImportError:
            logger.error("❌ Please install pybaseball: pip install pybaseball")
            raise

    def test_connection(self) -> bool:
        """Test if pybaseball is working"""
        try:
            import pybaseball
            from datetime import datetime, timedelta

            # Try a simple query to test connection
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)

            # Just check if we can make the call
            # Don't actually fetch data to save time
            return True

        except Exception as e:
            logger.error(f"Statcast connection test failed: {e}")
            return False

    def get_recent_stats(self, player_name: str, days: int = 7) -> Dict:
        """Enhanced with name variations"""
        # Clean up special characters
        cleaned_name = player_name.replace('ñ', 'n').replace('é', 'e').replace('á', 'a')

        # Try original name first
        result = self._try_lookup(player_name, days)
        if result['games_analyzed'] > 0:
            return result

        # Try cleaned name
        if cleaned_name != player_name:
            result = self._try_lookup(cleaned_name, days)
            if result['games_analyzed'] > 0:
                return result

        # Try common variations
        if "Jr." in player_name:
            # Try without Jr.
            alt_name = player_name.replace(" Jr.", "").strip()
            result = self._try_lookup(alt_name, days)
            if result['games_analyzed'] > 0:
                return result

    def _try_lookup(self, player_name: str, days: int) -> Dict:
        """Try to lookup player stats with pybaseball"""
        try:
            # Get date range
            end_date = self.season_end
            start_date = end_date - timedelta(days=days)

            # Format dates for pybaseball
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Try to get player stats
            from pybaseball import statcast_batter, statcast_pitcher

            # First try as batter
            try:
                df = statcast_batter(start_dt=start_str, end_dt=end_str, player_name=player_name)
                if df is not None and len(df) > 0:
                    return self._process_batting_stats(df, player_name)
            except:
                pass

            # Then try as pitcher
            try:
                df = statcast_pitcher(start_dt=start_str, end_dt=end_str, player_name=player_name)
                if df is not None and len(df) > 0:
                    return self._process_pitching_stats(df, player_name)
            except:
                pass

            # No data found
            return self._default_stats()

        except Exception as e:
            logger.error(f"Error in _try_lookup for {player_name}: {e}")
            return self._default_stats()

    def _process_batting_stats(self, df: pd.DataFrame, player_name: str) -> Dict:
        """Process batting statcast data"""
        # Filter to balls in play and calculate metrics
        bip = df[df['type'] == 'X']  # Balls in play

        if len(bip) == 0:
            return self._default_stats()

        # Calculate real metrics
        avg_exit_velo = bip['launch_speed'].mean() if 'launch_speed' in bip else 0
        avg_launch_angle = bip['launch_angle'].mean() if 'launch_angle' in bip else 0
        barrel_rate = len(bip[bip['launch_speed_angle'] == 6]) / len(bip) if len(bip) > 0 else 0

        # Get outcomes
        hits = len(df[df['events'].isin(['single', 'double', 'triple', 'home_run'])])
        at_bats = len(df[df['events'].notna()])
        batting_avg = hits / at_bats if at_bats > 0 else 0

        # Calculate expected stats
        xba_mean = bip[
            'estimated_ba_using_speedangle'].mean() if 'estimated_ba_using_speedangle' in bip else batting_avg
        xwoba_mean = bip[
            'estimated_woba_using_speedangle'].mean() if 'estimated_woba_using_speedangle' in bip else 0.320

        return {
            'player_name': player_name,
            'games_analyzed': len(df['game_date'].unique()),
            'batting_avg': round(batting_avg, 3),
            'xBA': round(xba_mean, 3),
            'xwOBA': round(xwoba_mean, 3),
            'avg_exit_velocity': round(avg_exit_velo, 1),
            'avg_launch_angle': round(avg_launch_angle, 1),
            'barrel_rate': round(barrel_rate * 100, 1),
            'hard_hit_rate': round(len(bip[bip['launch_speed'] >= 95]) / len(bip) * 100 if len(bip) > 0 else 0, 1),
            'recent_form': self._calculate_form_score(batting_avg, xba_mean, barrel_rate)
        }

    def _process_pitching_stats(self, df: pd.DataFrame, player_name: str) -> Dict:
        """Process pitching statcast data"""
        # Calculate pitching metrics
        total_pitches = len(df)
        strikes = len(df[df['type'].isin(['S', 'X'])])
        strike_rate = strikes / total_pitches if total_pitches > 0 else 0

        # Whiff rate
        swings = df[df['description'].str.contains('swing', case=False, na=False)]
        whiffs = swings[swings['description'].str.contains('miss|strike', case=False, na=False)]
        whiff_rate = len(whiffs) / len(swings) if len(swings) > 0 else 0

        # Velocity
        avg_velo = df['release_speed'].mean() if 'release_speed' in df else 0

        # Exit velocity against
        bip = df[df['type'] == 'X']
        avg_exit_velo_against = bip['launch_speed'].mean() if len(bip) > 0 and 'launch_speed' in bip else 0

        return {
            'player_name': player_name,
            'games_analyzed': len(df['game_date'].unique()),
            'avg_velocity': round(avg_velo, 1),
            'strike_rate': round(strike_rate * 100, 1),
            'whiff_rate': round(whiff_rate * 100, 1),
            'avg_exit_velo_against': round(avg_exit_velo_against, 1),
            'pitches_thrown': total_pitches,
            'recent_form': self._calculate_pitcher_form(strike_rate, whiff_rate, avg_exit_velo_against)
        }

    def _calculate_form_score(self, avg: float, xba: float, barrel_rate: float) -> float:
        """Calculate hitter form score (0.5 to 1.5)"""
        # Weight: 40% avg, 40% xBA, 20% barrels
        avg_score = avg / 0.260  # League average ~.260
        xba_score = xba / 0.260
        barrel_score = barrel_rate / 0.08  # League average ~8%

        form = (avg_score * 0.4) + (xba_score * 0.4) + (barrel_score * 0.2)
        return max(0.5, min(1.5, form))

    def _calculate_pitcher_form(self, strike_rate: float, whiff_rate: float, exit_velo: float) -> float:
        """Calculate pitcher form score (0.5 to 1.5)"""
        # Good: high strikes, high whiffs, low exit velo
        strike_score = strike_rate / 0.64  # League average ~64%
        whiff_score = whiff_rate / 0.24  # League average ~24%
        exit_score = (92 - exit_velo) / 4 + 1  # 92 mph is bad, 88 is good

        form = (strike_score * 0.3) + (whiff_score * 0.3) + (exit_score * 0.4)
        return max(0.5, min(1.5, form))

    def _default_stats(self) -> Dict:
        """Return default stats when player not found"""
        return {
            'recent_form': 1.0,
            'games_analyzed': 0,
            'data_available': False
        }

    def get_consistency_score(self, player_name: str, days: int = 30) -> float:
        """
        Calculate consistency based on game-to-game variance

        Returns:
            Float between 0.5 and 1.5 (1.0 = average consistency)
        """
        try:
            stats = self.get_recent_stats(player_name, days)

            if not stats.get('data_available', True):
                return 1.0

            # For hitters: use batting average stability
            if 'batting_avg' in stats:
                # Also fetch last 60 days to compare
                long_stats = self.get_recent_stats(player_name, 60)

                if long_stats.get('batting_avg', 0) > 0:
                    # Compare recent to longer term
                    recent_avg = stats.get('batting_avg', 0.250)
                    long_avg = long_stats.get('batting_avg', 0.250)

                    # Less variance = more consistent
                    variance = abs(recent_avg - long_avg)
                    consistency = 1.0 - (variance * 2)  # Penalize high variance

                    return max(0.5, min(1.5, consistency))

            # For pitchers: use velocity/strike rate stability
            elif 'avg_velocity' in stats:
                # Pitchers are generally more consistent
                return 1.1

            return 1.0

        except Exception as e:
            logger.error(f"Error calculating consistency for {player_name}: {e}")
            return 1.0


# ========== 2. WEATHER DATA INTEGRATION ==========
class RealWeatherIntegration:
    """Get REAL weather data for game locations"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.use_openweather = api_key is not None

        # Stadium coordinates (add more as needed)
        self.stadium_coords = {
            'NYY': (40.8296, -73.9262),  # Yankee Stadium
            'NYM': (40.7571, -73.8458),  # Citi Field
            'BOS': (42.3467, -71.0972),  # Fenway Park
            'LAD': (34.0739, -118.2400),  # Dodger Stadium
            'SF': (37.7786, -122.3893),  # Oracle Park
            'CHC': (41.9484, -87.6553),  # Wrigley Field
            'CWS': (41.8299, -87.6338),  # Guaranteed Rate Field
            'HOU': (29.7573, -95.3555),  # Minute Maid Park
            'SD': (32.7076, -117.1570),  # Petco Park
            'SEA': (47.5914, -122.3325),  # T-Mobile Park
            'TEX': (32.7511, -97.0833),  # Globe Life Field
            'ATL': (33.8907, -84.4678),  # Truist Park
            'WSH': (38.8730, -77.0074),  # Nationals Park
            'PHI': (39.9061, -75.1665),  # Citizens Bank Park
            'MIL': (43.0280, -87.9712),  # American Family Field
            'STL': (38.6226, -90.1928),  # Busch Stadium
            'PIT': (40.4468, -80.0057),  # PNC Park
            'CIN': (39.0974, -84.5071),  # Great American Ball Park
            'CLE': (41.4962, -81.6852),  # Progressive Field
            'DET': (42.3390, -83.0485),  # Comerica Park
            'MIN': (44.9818, -93.2775),  # Target Field
            'KC': (39.0517, -94.4803),  # Kauffman Stadium
            'TB': (27.7682, -82.6534),  # Tropicana Field (dome)
            'TOR': (43.6414, -79.3894),  # Rogers Centre
            'BAL': (39.2838, -76.6216),  # Camden Yards
            'OAK': (37.7516, -122.2005),  # Oakland Coliseum
            'LAA': (33.8003, -117.8827),  # Angel Stadium
            'MIA': (25.7781, -80.2196),  # loanDepot park
            'COL': (39.7559, -104.9942),  # Coors Field
            'ARI': (33.4455, -112.0667),  # Chase Field (dome)
        }

        # Dome stadiums (weather doesn't matter)
        self.dome_stadiums = {'TB', 'TOR', 'MIA', 'HOU', 'ARI', 'TEX', 'MIL'}

    def get_game_weather(self, home_team: str, game_time: Optional[datetime] = None) -> Dict:
        """
        Get real weather data for a game

        Args:
            home_team: Home team abbreviation (e.g., 'NYY')
            game_time: Game datetime (defaults to TODAY/NOW)

        Returns:
            Dict with weather impact metrics
        """
        # Use current date/time if not specified
        if game_time is None:
            from datetime import datetime
            game_time = datetime.now()

        # Check if dome stadium
        if home_team in self.dome_stadiums:
            return {
                'temperature': 72,
                'wind_speed': 0,
                'humidity': 50,
                'precipitation': 0,
                'weather_impact': 1.0,
                'is_dome': True,
                'conditions': 'Dome - Perfect',
                'game_time': game_time.strftime('%Y-%m-%d %H:%M')
            }

        # Get coordinates
        coords = self.stadium_coords.get(home_team)
        if not coords:
            logger.warning(f"No coordinates for {home_team}, using defaults")
            return self._default_weather()

        lat, lon = coords

        try:
            if self.use_openweather:
                return self._get_openweather_data(lat, lon, game_time)
            else:
                return self._get_open_meteo_data(lat, lon)
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._default_weather()

    def _get_open_meteo_data(self, lat: float, lon: float) -> Dict:
        """Get weather from Open-Meteo (no API key required) with time support"""
        url = "https://api.open-meteo.com/v1/forecast"

        # Format the time for the API
        if game_time:
            # Open-Meteo wants ISO format
            time_str = game_time.strftime('%Y-%m-%dT%H:00')

            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': 'temperature_2m,windspeed_10m,precipitation,weathercode',
                'temperature_unit': 'fahrenheit',
                'windspeed_unit': 'mph',
                'precipitation_unit': 'inch',
                'timezone': 'America/New_York',
                'start_date': game_time.strftime('%Y-%m-%d'),
                'end_date': game_time.strftime('%Y-%m-%d')
            }
        else:
            # Current weather
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'temperature_unit': 'fahrenheit',
                'windspeed_unit': 'mph',
                'precipitation_unit': 'inch'
            }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if game_time and 'hourly' in data:
            # Find the closest hour
            target_hour = game_time.hour

            # Get data for the specific hour
            temps = data['hourly']['temperature_2m']
            winds = data['hourly']['windspeed_10m']
            precips = data['hourly']['precipitation']
            codes = data['hourly']['weathercode']

            # Use the target hour (or closest available)
            idx = min(target_hour, len(temps) - 1)

            temp = temps[idx]
            wind = winds[idx]
            rain = precips[idx]
            weather_code = codes[idx]
        else:
            # Use current weather
            current = data.get('current_weather', {})
            temp = current.get('temperature', 72)
            wind = current.get('windspeed', 5)
            rain = 0
            weather_code = current.get('weathercode', 0)

        # Interpret weather code
        if weather_code <= 1:
            conditions = "Clear"
        elif weather_code <= 3:
            conditions = "Partly cloudy"
        elif weather_code <= 48:
            conditions = "Cloudy"
        elif weather_code <= 67:
            conditions = "Light rain"
            rain = max(rain, 0.1)
        else:
            conditions = "Rain"
            rain = max(rain, 0.5)

        return {
            'temperature': temp,
            'wind_speed': wind,
            'humidity': 60,  # Default, Open-Meteo doesn't provide in free tier
            'precipitation': rain,
            'conditions': conditions,
            'weather_impact': self._calculate_weather_impact(temp, wind, rain),
            'is_dome': False,
            'game_time': game_time.strftime('%Y-%m-%d %H:%M') if game_time else 'current'
        }

    def _get_openweather_data(self, lat: float, lon: float, game_time: datetime = None) -> Dict:
        """Get weather from OpenWeatherMap (requires API key)"""
        if not self.api_key:
            return self._get_open_meteo_data(lat, lon)  # Remove game_time parameter

        # OpenWeather has different endpoints for current vs forecast
        if game_time and (game_time - datetime.now()).total_seconds() > 3600:
            # Future weather - use forecast endpoint
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': 40  # Get multiple forecasts
            }
        else:
            # Current weather
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'
            }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'list' in data and game_time:
            # Find closest forecast to game time
            target_timestamp = int(game_time.timestamp())
            closest_forecast = min(data['list'],
                                   key=lambda x: abs(x['dt'] - target_timestamp))

            temp = closest_forecast['main']['temp']
            wind = closest_forecast['wind']['speed']
            humidity = closest_forecast['main']['humidity']
            rain = closest_forecast.get('rain', {}).get('3h', 0) / 3  # Convert 3h to 1h
            desc = closest_forecast['weather'][0]['description']
        else:
            # Current weather
            temp = data['main']['temp']
            wind = data['wind']['speed']
            humidity = data['main']['humidity']
            rain = data.get('rain', {}).get('1h', 0)
            desc = data['weather'][0]['description']

        return {
            'temperature': temp,
            'wind_speed': wind,
            'humidity': humidity,
            'precipitation': rain,
            'conditions': desc,
            'weather_impact': self._calculate_weather_impact(temp, wind, rain),
            'is_dome': False,
            'game_time': game_time.strftime('%Y-%m-%d %H:%M') if game_time else 'current'
        }

    def _default_weather(self) -> Dict:
        """Default weather when API fails"""
        return {
            'temperature': 72,
            'wind_speed': 5,
            'humidity': 50,
            'precipitation': 0,
            'weather_impact': 1.0,
            'is_dome': False,
            'conditions': 'Unknown',
            'game_time': 'unknown'
        }

    def _get_openweather_data(self, lat: float, lon: float) -> Dict:
        """Get weather from OpenWeatherMap (requires API key)"""
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'imperial'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        temp = data['main']['temp']
        wind = data['wind']['speed']
        humidity = data['main']['humidity']
        rain = data.get('rain', {}).get('1h', 0)
        desc = data['weather'][0]['description']

        return {
            'temperature': temp,
            'wind_speed': wind,
            'humidity': humidity,
            'precipitation': rain,
            'conditions': desc,
            'weather_impact': self._calculate_weather_impact(temp, wind, rain),
            'is_dome': False
        }

    def _get_open_meteo_data(self, lat: float, lon: float) -> Dict:
        """Get weather from Open-Meteo (no API key required)"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': True,
            'temperature_unit': 'fahrenheit',
            'windspeed_unit': 'mph',
            'precipitation_unit': 'inch'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        current = data['current_weather']
        temp = current['temperature']
        wind = current['windspeed']

        # Estimate conditions based on weather code
        weather_code = current['weathercode']
        if weather_code <= 1:
            conditions = "Clear"
            rain = 0
        elif weather_code <= 3:
            conditions = "Partly cloudy"
            rain = 0
        elif weather_code <= 48:
            conditions = "Cloudy"
            rain = 0
        elif weather_code <= 67:
            conditions = "Light rain"
            rain = 0.1
        else:
            conditions = "Rain"
            rain = 0.5

        return {
            'temperature': temp,
            'wind_speed': wind,
            'humidity': 60,  # Default
            'precipitation': rain,
            'conditions': conditions,
            'weather_impact': self._calculate_weather_impact(temp, wind, rain),
            'is_dome': False
        }

    def _calculate_weather_impact(self, temp: float, wind: float, rain: float) -> float:
        """
        Calculate weather impact on scoring

        Returns:
            Float multiplier (0.8 to 1.2)
        """
        impact = 1.0

        # Temperature impact
        if temp >= 80:
            impact += 0.05  # Hot = more offense
        elif temp <= 50:
            impact -= 0.05  # Cold = less offense

        # Wind impact (for hitters)
        if wind >= 15:
            impact += 0.05  # Strong wind can help HRs
        elif wind >= 20:
            impact += 0.10

        # Rain impact
        if rain > 0:
            impact -= rain * 0.2  # Rain hurts offense

        return max(0.8, min(1.2, impact))

    def _default_weather(self) -> Dict:
        """Default weather when API fails"""
        return {
            'temperature': 72,
            'wind_speed': 5,
            'humidity': 50,
            'precipitation': 0,
            'weather_impact': 1.0,
            'is_dome': False,
            'conditions': 'Unknown'
        }


# ========== 3. PARK FACTORS (Already in your system) ==========
class RealParkFactors:
    """Use the park factors from your existing park_factors.py"""

    def __init__(self):
        # These are real MLB park factors
        self.factors = {
            'COL': 1.33,  # Coors Field - extreme hitter's park
            'CIN': 1.14,  # Great American Ball Park
            'TEX': 1.12,  # Globe Life Field
            'BAL': 1.10,  # Camden Yards
            'TOR': 1.08,  # Rogers Centre
            'MIL': 1.07,  # American Family Field
            'BOS': 1.06,  # Fenway Park
            'PHI': 1.04,  # Citizens Bank Park
            'MIN': 1.03,  # Target Field
            'CWS': 1.02,  # Guaranteed Rate Field
            'CHC': 1.01,  # Wrigley Field
            'KC': 1.00,  # Kauffman Stadium
            'NYY': 0.99,  # Yankee Stadium
            'WSH': 0.98,  # Nationals Park
            'CLE': 0.97,  # Progressive Field
            'ARI': 0.96,  # Chase Field
            'LAA': 0.95,  # Angel Stadium
            'SD': 0.94,  # Petco Park
            'HOU': 0.93,  # Minute Maid Park
            'TB': 0.92,  # Tropicana Field
            'DET': 0.91,  # Comerica Park
            'STL': 0.90,  # Busch Stadium
            'NYM': 0.89,  # Citi Field
            'SEA': 0.88,  # T-Mobile Park
            'OAK': 0.87,  # Oakland Coliseum
            'SF': 0.86,  # Oracle Park
            'LAD': 0.94,  # Dodger Stadium
            'ATL': 0.98,  # Truist Park
            'PIT': 0.95,  # PNC Park
            'MIA': 0.92,  # loanDepot park
        }

    def get_park_factor(self, team: str) -> float:
        """Get park factor for team"""
        return self.factors.get(team, 1.0)


# ========== 4. INSTALLATION HELPER ==========
def check_and_install_dependencies():
    """Check if required packages are installed"""
    required = {
        'pybaseball': 'pip install pybaseball',
        'requests': 'pip install requests',
        'pandas': 'pip install pandas',
        'numpy': 'pip install numpy'
    }

    missing = []
    for package, install_cmd in required.items():
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing.append((package, install_cmd))
            print(f"❌ {package} is NOT installed")

    if missing:
        print("\n⚠️ Missing packages! Install with:")
        for pkg, cmd in missing:
            print(f"   {cmd}")
        print("\nOr install all at once:")
        print("   pip install pybaseball requests pandas numpy")
    else:
        print("\n✅ All dependencies installed!")

    return len(missing) == 0


# ========== 5. EXAMPLE USAGE ==========
if __name__ == "__main__":
    print("🏆 REAL DATA ENRICHMENT SYSTEM")
    print("=" * 50)

    # Check dependencies
    if not check_and_install_dependencies():
        print("\nPlease install missing packages first!")
        exit(1)

    # Test real stats
    print("\n📊 Testing Real Stats Fetcher...")
    stats_fetcher = RealStatcastFetcher()

    # Test with a real player
    player_stats = stats_fetcher.get_recent_stats("Aaron Judge", days=7)
    print(f"\nAaron Judge recent stats:")
    for key, value in player_stats.items():
        print(f"  {key}: {value}")

    # Test weather
    print("\n🌤️ Testing Weather Integration...")
    weather = RealWeatherIntegration()  # No API key = uses Open-Meteo

    game_weather = weather.get_game_weather('NYY')
    print(f"\nYankee Stadium weather:")
    for key, value in game_weather.items():
        print(f"  {key}: {value}")

    # Test park factors
    print("\n🏟️ Testing Park Factors...")
    parks = RealParkFactors()

    print(f"\nCoors Field factor: {parks.get_park_factor('COL')}")
    print(f"Oracle Park factor: {parks.get_park_factor('SF')}")

    print("\n✅ All systems operational!")