# REPLACE the calculate_enhanced_score method in unified_player_model.py with:

def calculate_enhanced_score(self):
    """Calculate score using ONLY the new enhanced scoring engine"""
    from enhanced_scoring_engine import EnhancedScoringEngine
    
    # Create scoring engine
    engine = EnhancedScoringEngine()
    
    # Default to GPP scoring (can be changed based on context)
    self.enhanced_score = engine.score_player_gpp(self)
    
    # Also calculate and store other contest scores
    self.gpp_score = self.enhanced_score
    self.cash_score = engine.score_player_cash(self)
    self.showdown_score = engine.score_player_showdown(self)
    
    # Set data quality based on available data
    data_points = 0
    if hasattr(self, 'implied_team_score') and self.implied_team_score: data_points += 1
    if hasattr(self, 'batting_order') and self.batting_order: data_points += 1
    if hasattr(self, 'projected_ownership'): data_points += 1
    if hasattr(self, 'recent_form_score'): data_points += 1
    
    self.data_quality_score = min(1.0, 0.2 + (data_points * 0.2))
    
    return self.enhanced_score

# ADD this new method to switch contest types:
def set_contest_type(self, contest_type: str):
    """Set which score to use as enhanced_score"""
    from enhanced_scoring_engine import EnhancedScoringEngine
    engine = EnhancedScoringEngine()
    
    if contest_type.lower() == 'cash':
        self.enhanced_score = engine.score_player_cash(self)
    elif contest_type.lower() == 'showdown':
        self.enhanced_score = engine.score_player_showdown(self)
    else:  # Default to GPP
        self.enhanced_score = engine.score_player_gpp(self)
