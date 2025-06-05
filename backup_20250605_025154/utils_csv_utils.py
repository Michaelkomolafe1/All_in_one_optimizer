#!/usr/bin/env python3
"""
Optimized CSV Reading Utilities
Reduces multiple file reads and improves parsing performance
"""

import csv
import os
from typing import Dict, List, Optional, Iterator, Any
from functools import lru_cache

class OptimizedCSVReader:
    """Optimized CSV reader with caching and smart parsing"""

    def __init__(self):
        self._file_cache = {}

    @lru_cache(maxsize=10)
    def detect_delimiter(self, file_path: str) -> str:
        """Detect CSV delimiter automatically"""
        try:
            with open(file_path, 'r') as f:
                sample = f.read(1024)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=',\t;|')
                return dialect.delimiter
        except:
            return ','

    def read_csv_once(self, file_path: str, cache_key: str = None) -> List[Dict]:
        """Read CSV file once and cache results"""

        if not cache_key:
            cache_key = os.path.basename(file_path)

        # Return cached data if available
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        # Read file
        data = []
        delimiter = self.detect_delimiter(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = list(reader)

        # Cache the data
        self._file_cache[cache_key] = data
        return data

    def process_dk_file(self, file_path: str) -> List[Dict]:
        """Optimized DraftKings file processing"""

        raw_data = self.read_csv_once(file_path, 'dk_file')
        processed_players = []

        for row in raw_data:
            # Extract with fallbacks
            player = {
                'id': row.get('ID', '0'),
                'name': row.get('Name', ''),
                'position': row.get('Roster Position', row.get('Position', '')),
                'team': row.get('TeamAbbrev', ''),
                'salary': self._parse_salary(row.get('Salary', '0')),
                'projection': self._parse_float(row.get('AvgPointsPerGame', '0')),
                'game_info': row.get('Game Info', ''),
            }

            # Calculate score
            player['score'] = player['projection'] if player['projection'] > 0 else player['salary'] / 1000.0

            processed_players.append(player)

        return processed_players

    def _parse_salary(self, salary_str: str) -> int:
        """Parse salary string to integer"""
        try:
            clean_str = str(salary_str).replace('$', '').replace(',', '').strip()
            return int(float(clean_str))
        except:
            return 3000

    def _parse_float(self, float_str: str) -> float:
        """Parse float string safely"""
        try:
            return float(str(float_str).replace(',', '').strip())
        except:
            return 0.0

    def clear_cache(self):
        """Clear file cache"""
        self._file_cache.clear()

# Global CSV reader instance
csv_reader = OptimizedCSVReader()
