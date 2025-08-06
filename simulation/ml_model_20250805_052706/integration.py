#!/usr/bin/env python3
"""
ML OPTIMIZER INTEGRATION
========================
"""

import pickle
import pandas as pd
import numpy as np
import os

class MLOptimizer:
    def __init__(self, model_dir="ml_model_20250805_052706"):
        with open(os.path.join(model_dir, 'model.pkl'), 'rb') as f:
            self.model = pickle.load(f)
        self.features = ['salary', 'projection', 'optimization_score', 'value_score', 'slate_size_encoded', 'is_cash', 'strategy_fit', 'difficulty_encoded']

    def enhance_players(self, players, slate_size='medium', contest_type='gpp'):
        """Enhance player scores with ML predictions"""

        # Prepare data
        data = []
        for p in players:
            row = {
                'salary': getattr(p, 'salary', 5000),
                'projection': getattr(p, 'base_projection', 10),
                'optimization_score': getattr(p, 'optimization_score', 10),
                'value_score': 0,  # Calculate below
                'slate_size_encoded': {'small': 0, 'medium': 1, 'large': 2}.get(slate_size, 1),
                'is_cash': 1 if contest_type == 'cash' else 0,
                'strategy_fit': 1.0,
                'difficulty_encoded': 1  # Medium
            }

            # Calculate value
            if row['salary'] > 0:
                row['value_score'] = row['projection'] / (row['salary'] / 1000)

            data.append(row)

        # Predict
        df = pd.DataFrame(data)
        X = df[self.features].fillna(0)
        probs = self.model.predict_proba(X)[:, 1]

        # Apply adjustments
        for player, prob in zip(players, probs):
            if prob > 0.5:
                boost = 1.0 + (prob - 0.5) * 0.2
            else:
                boost = 0.95

            player.ml_score = prob
            player.ml_boost = boost

            if hasattr(player, 'optimization_score'):
                player.optimization_score *= boost

        return players

# Usage:
# from ml_model_20250805_052706.integration import MLOptimizer
# ml = MLOptimizer()
# enhanced_players = ml.enhance_players(players, slate_size='medium', contest_type='gpp')
