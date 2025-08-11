#!/usr/bin/env python3
"""
Weather Integration for DFS Scoring
==================================
Fetches real weather data and calculates impact on scoring
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data for a game"""
    temperature: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    humidity: float
    condition: str
    game_time_weather: bool = True  # Whether this is game-time weather


class WeatherIntegration:
    """Handles weather data fetching and impact calculations"""

    # Stadium coordinates for weather lookup
    STADIUM_COORDS = {
        'ATL': (33.7555, -84.3900),  # Truist Park
        'ARI': (33.4455, -112.0667),  # Chase Field (dome)
        'BAL': (39.2838, -76.6217),  # Camden Yards
        'BOS': (42.3467, -71.0972),  # Fenway Park
        'CHC': (41.9484, -87.6553),  # Wrigley Field
        'CWS': (41.8299, -87.6338),  # Guaranteed Rate Field
        'CIN': (39.0974, -84.5071),  # Great American Ball Park
        'CLE': (41.4962, -81.6852),  # Progressive Field
        'COL': (39.7559, -104.9942),  # Coors Field
        'DET': (42.3390, -83.0485),  # Comerica Park
        'HOU': (29.7573, -95.3555),  # Minute Maid Park (retractable)
        'KC': (39.0517, -94.4803),  # Kauffman Stadium
        'LAA': (33.8003, -117.8827),  # Angel Stadium
        'LAD': (34.0739, -118.2400),  # Dodger Stadium
        'MIA': (25.7781, -80.2196),  # Marlins Park (retractable)
        'MIL': (43.0280, -87.9712),  # American Family Field (retractable)
        'MIN': (44.9817, -93.2776),  # Target Field
        'NYM': (40.7571, -73.8458),  # Citi Field
        'NYY': (40.8296, -73.9262),  # Yankee Stadium
        'OAK': (37.7516, -122.2005),  # Oakland Coliseum
        'PHI': (39.9061, -75.1665),  # Citizens Bank Park
        'PIT': (40.4468, -80.0057),  # PNC Park
        'SD': (32.7076, -117.1570),  # Petco Park
        'SEA': (47.5914, -122.3325),  # T-Mobile Park (retractable)
        'SF': (37.7786, -122.3893),  # Oracle Park
        'STL': (38.6226, -90.1928),  # Busch Stadium
        'TB': (27.7682, -82.6534),  # Tropicana Field (dome)
        'TEX': (32.7512, -97.0832),  # Globe Life Field (retractable)
        'TOR': (43.6414, -79.3894),  # Rogers Centre (retractable)
        'WAS': (38.8730, -77.0074),  # Nationals Park
    }
    TEAM_MAPPINGS = {
        # DraftKings sometimes uses different codes
        'WSH': 'WAS',  # Washington
        'ATH': 'ATL',  # Atlanta (Athletics? Mapped to Braves)
        'CHW': 'CWS',  # White Sox
        # Add any other mismatches you find
    }

    # Dome/Retractable roof stadiums (weather doesn't matter as much)
    DOME_STADIUMS = {'ARI', 'TB'}  # Fixed domes
    RETRACTABLE_STADIUMS = {'HOU', 'MIA', 'MIL', 'SEA', 'TEX', 'TOR'}

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key for weather service"""
        self.api_key = api_key or self._get_free_weather_key()
        self._cache = {}

    def _get_free_weather_key(self) -> str:
        """Use free weather API (OpenWeatherMap free tier)"""
        # You can get a free key at: https://openweathermap.org/api
        # For now, return empty - user should set their own
        return ""

    def get_weather_for_game(self, team: str, game_time: Optional[datetime] = None) -> WeatherData:
        """Get weather data for a team's stadium"""

        # Map team code if needed
        team = self.TEAM_MAPPINGS.get(team, team)

        # Check dome/retractable
        if team in self.DOME_STADIUMS:
            return self._get_dome_weather(
                temperature=72.0,  # Climate controlled
                wind_speed=0.0,
                wind_direction="N/A",
                precipitation=0.0,
                humidity=50.0,
                condition="Dome",
                game_time_weather=True
            )

        # Get coordinates
        coords = self.STADIUM_COORDS.get(team)
        if not coords:
            logger.warning(f"No coordinates for team {team}")
            return self._get_default_weather()

        # Check cache
        cache_key = f"{team}_{datetime.now().strftime('%Y%m%d_%H')}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Fetch weather
        try:
            if self.api_key:
                weather = self._fetch_weather_api(coords[0], coords[1])
            else:
                weather = self._fetch_weather_free(coords[0], coords[1])

            self._cache[cache_key] = weather
            return weather

        except Exception as e:
            logger.error(f"Weather fetch failed for {team}: {e}")
            return self._get_default_weather()

    def _fetch_weather_api(self, lat: float, lon: float) -> WeatherData:
        """Fetch from OpenWeatherMap API"""
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'imperial'
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        return WeatherData(
            temperature=data['main']['temp'],
            wind_speed=data['wind']['speed'],
            wind_direction=self._degrees_to_direction(data['wind'].get('deg', 0)),
            precipitation=data.get('rain', {}).get('1h', 0.0),
            humidity=data['main']['humidity'],
            condition=data['weather'][0]['main']
        )

    def _fetch_weather_free(self, lat: float, lon: float) -> WeatherData:
        """Fetch from free weather service (wttr.in)"""
        try:
            url = f"https://wttr.in/{lat},{lon}?format=j1"
            response = requests.get(url, timeout=5)
            data = response.json()

            current = data['current_condition'][0]

            return WeatherData(
                temperature=float(current['temp_F']),
                wind_speed=float(current['windspeedMiles']),
                wind_direction=current['winddir16Point'],
                precipitation=float(current.get('precipMM', 0)) / 25.4,  # Convert to inches
                humidity=float(current['humidity']),
                condition=current['weatherDesc'][0]['value']
            )
        except:
            return self._get_default_weather()

    def _get_default_weather(self) -> WeatherData:
        """Return neutral weather conditions"""
        return WeatherData(
            temperature=75.0,
            wind_speed=5.0,
            wind_direction="N",
            precipitation=0.0,
            humidity=50.0,
            condition="Clear"
        )

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to direction"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]

    def calculate_weather_impact(self, weather: WeatherData, is_pitcher: bool = False) -> float:
        """
        Calculate weather impact multiplier (0.5 to 1.5)

        Factors:
        - Temperature: 50-95°F range (cold hurts hitting)
        - Wind: Out = hitting+, In = pitching+
        - Precipitation: Always bad for hitting
        - Humidity: High = hitting+ (ball carries)
        """

        # Dome = neutral
        if weather.condition == "Dome":
            return 1.0

        multiplier = 1.0

        # Temperature impact (optimal 75-85°F)
        if weather.temperature < 50:
            temp_factor = 0.85  # Very cold
        elif weather.temperature < 60:
            temp_factor = 0.90  # Cold
        elif weather.temperature < 70:
            temp_factor = 0.95  # Cool
        elif weather.temperature <= 85:
            temp_factor = 1.05  # Optimal
        elif weather.temperature <= 95:
            temp_factor = 1.03  # Hot (still good)
        else:
            temp_factor = 0.98  # Very hot

        # Wind impact
        wind_factor = 1.0
        if weather.wind_speed > 10:
            if weather.wind_direction in ['S', 'SW', 'SE']:  # Generally out
                wind_factor = 1.10 if not is_pitcher else 0.90
            elif weather.wind_direction in ['N', 'NE', 'NW']:  # Generally in
                wind_factor = 0.90 if not is_pitcher else 1.10

        # Precipitation impact
        precip_factor = 1.0
        if weather.precipitation > 0.1:
            precip_factor = 0.85  # Rain hurts hitting

        # Humidity impact (high humidity = ball carries)
        humidity_factor = 1.0
        if weather.humidity > 70:
            humidity_factor = 1.03 if not is_pitcher else 0.97
        elif weather.humidity < 30:
            humidity_factor = 0.97 if not is_pitcher else 1.03

        # Combine factors
        multiplier = temp_factor * wind_factor * precip_factor * humidity_factor

        # Apply pitcher inversion if needed
        if is_pitcher:
            # Don't fully invert, just dampen the effect
            multiplier = 1.0 + (multiplier - 1.0) * -0.7

        # Bound between 0.80 and 1.20
        return max(0.80, min(1.20, multiplier))

    def get_weather_description(self, weather: WeatherData) -> str:
        """Get human-readable weather description"""
        if weather.condition == "Dome":
            return "Indoor (Dome)"

        desc = f"{weather.temperature:.0f}°F, "
        desc += f"{weather.condition}, "
        desc += f"{weather.wind_speed:.0f} mph {weather.wind_direction}"

        if weather.precipitation > 0:
            desc += f", Rain: {weather.precipitation:.1f}\""

        return desc


# Singleton instance
_weather_instance = None


def get_weather_integration(api_key: Optional[str] = None) -> WeatherIntegration:
    """Get or create weather integration instance"""
    global _weather_instance

    if _weather_instance is None:
        _weather_instance = WeatherIntegration(api_key)
    elif api_key:
        _weather_instance.api_key = api_key

    return _weather_instance


if __name__ == "__main__":
    # Test weather integration
    weather = get_weather_integration()

    print("🌦️ Weather Integration Test")
    print("=" * 50)

    # Test a few stadiums
    for team in ['COL', 'NYY', 'TB', 'LAD']:
        data = weather.get_weather_for_game(team)
        impact = weather.calculate_weather_impact(data)
        desc = weather.get_weather_description(data)

        print(f"\n{team}: {desc}")
        print(f"   Impact: {impact:.2f}x")