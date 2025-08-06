# CONSOLIDATION GUIDE
======================

## 1. SCORING ENGINES - Consolidate into ONE file

Create `main_optimizer/unified_scoring.py` with:
```python
"""Unified Scoring System"""

class UnifiedScoringEngine:
    def __init__(self, **kwargs):
        # Accept any kwargs for compatibility
        for key, value in kwargs.items():
            setattr(self, key, value)

    def score_player(self, player, contest_type='gpp'):
        if contest_type == 'cash':
            return self.score_player_cash(player)
        elif contest_type == 'showdown':
            return self.score_player_showdown(player)
        else:
            return self.score_player_gpp(player)

    def score_player_gpp(self, player):
        # GPP scoring logic
        base = getattr(player, 'base_projection', 10.0)
        # Add GPP adjustments
        return base * 1.1

    def score_player_cash(self, player):
        # Cash scoring logic
        base = getattr(player, 'base_projection', 10.0)
        # Add floor emphasis
        return base * 0.95

    def score_player_showdown(self, player):
        # Showdown scoring
        return self.score_player_gpp(player) * 1.1

# Aliases for compatibility
EnhancedScoringEngineV2 = UnifiedScoringEngine
EnhancedScoringEngine = UnifiedScoringEngine
```

Then DELETE:
- enhanced_scoring_engine.py
- enhanced_scoring_engine_v2.py
- pure_data_scoring_engine.py
- vegas_scoring_engine.py (if exists)

## 2. STRATEGIES - Consolidate into TWO files

### `main_optimizer/cash_strategies.py`:
- Keep all cash game strategies

### `main_optimizer/gpp_strategies.py`:
- Keep all GPP/tournament strategies

DELETE separate strategy files like:
- tournament_winner_gpp_strategy.py
- individual strategy files

## 3. REQUIREMENTS - Use Minimal Version

Create `requirements.txt`:
```
pandas>=1.3.0
numpy>=1.21.0
pulp>=2.5.0
PyQt5>=5.15.0
```

Remove ortools since you don't use it!

## 4. FILES YOU CAN SAFELY DELETE

- Any __pycache__ directories
- Any .backup or .bak files
- Any _old or _copy files
- Empty or near-empty .py files
- Test files you're not using
