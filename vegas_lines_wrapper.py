"""Wrapper to make new API compatible with existing code"""

from vegas_lines_api import VegasLinesAPI

class VegasLines(VegasLinesAPI):
    """Compatibility wrapper"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.verbose = kwargs.get('verbose', False)
    
    def get_vegas_lines(self, **kwargs):
        """Compatible method name"""
        return self.get_mlb_totals()
    
    def apply_to_players(self, players):
        """Compatible method name"""
        self.enrich_players(players)
        return players
