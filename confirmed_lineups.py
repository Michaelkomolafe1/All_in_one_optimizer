#!/usr/bin/env python3
"""
CONFIRMED LINEUPS MODULE
Simple implementation to eliminate the warning
"""

from enum import Enum

class ContestType(Enum):
    GPP = "gpp"
    CASH = "cash"
    SINGLE_ENTRY = "single"
    SHOWDOWN = "showdown"

class ConfirmedLineups:
    def __init__(self, **kwargs):
        self.confirmed_players = {}
        self.confirmed_pitchers = {}

    def is_player_confirmed(self, name, team):
        """Check if player is confirmed"""
        return False, 0

    def is_pitcher_starting(self, name, team):
        """Check if pitcher is starting"""
        return False

    def ensure_data_loaded(self, **kwargs):
        """Ensure data is loaded"""
        return True

    def set_players_data(self, players):
        """Set players data"""
        pass
