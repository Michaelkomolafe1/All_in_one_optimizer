#!/usr/bin/env python3
"""
QUICK ML TRAINER
================
Trains a simple XGBoost model on your combined data
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
import os


def train_ml_model(csv_file):
    """Train ML model on combined data"""

    print("🤖 QUICK ML TRAINER")
    print("=" * 50)

    # Load data
    print(f"\n📂 Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"   Records: {len(df):,}")

    # Define features - only use what's available
    base_features = [
        'salary', 'projection', 'optimization_score',
        'lineup_score', 'lineup_rank'
    ]

    # Check which features are actually available
    available_features = [f for f in base_features if f in df.columns]
    print(f"\n📊 Using features: {available_features}")

    # Prepare target - player exceeded projection?
    # Since we don't have actual_score, use lineup success as proxy
    df['target'] = df['lineup_win'].astype(float)

    # Add some engineered features
    if 'salary' in df.columns and 'projection' in df.columns:
        df['value_score'] = df['projection'] / (df['salary'] / 1000)
        available_features.append('value_score')

    if 'lineup_rank' in df.columns:
        df['rank_percentile'] = (100 - df['lineup_rank']) / 100
        available_features.append('rank_percentile')

    # Add difficulty as a feature
    if 'difficulty_level' in df.columns:
        difficulty_map = {'easy': 0, 'medium': 1, 'hard': 2, 'extreme': 3}
        df['difficulty_numeric'] = df['difficulty_level'].map(difficulty_map).fillna(1)
        available_features.append('difficulty_numeric')

    # Clean data
    X = df[available_features].fillna(0)
    y = df['target']

    print(f"\n🔧 Training data shape: {X.shape}")
    print(f"   Positive examples: {y.sum():,} ({y.mean() * 100:.1f}%)")

    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    try:
        import xgboost as xgb
        print("\n🚀 Training XGBoost model...")

        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic',
            random_state=42,
            scale_pos_weight=len(y_train) / y_train.sum()  # Handle imbalanced data
        )

        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=10,
            verbose=False
        )

        # Evaluate
        from sklearn.metrics import accuracy_score, roc_auc_score

        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        test_pred_proba = model.predict_proba(X_test)[:, 1]

        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        test_auc = roc_auc_score(y_test, test_pred_proba)

        print(f"\n📈 Model Performance:")
        print(f"   Train Accuracy: {train_acc * 100:.1f}%")
        print(f"   Test Accuracy: {test_acc * 100:.1f}%")
        print(f"   Test AUC: {test_auc:.3f}")

        # Feature importance
        print(f"\n🎯 Feature Importance:")
        importance_df = pd.DataFrame({
            'feature': available_features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        for _, row in importance_df.iterrows():
            print(f"   {row['feature']:20s}: {row['importance']:.3f}")

        # Save model
        output_dir = f"ml_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)

        model_file = os.path.join(output_dir, 'xgb_model.pkl')
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)

        # Save feature list
        feature_file = os.path.join(output_dir, 'features.txt')
        with open(feature_file, 'w') as f:
            f.write('\n'.join(available_features))

        # Save model info
        info_file = os.path.join(output_dir, 'model_info.txt')
        with open(info_file, 'w') as f:
            f.write(f"Training Date: {datetime.now()}\n")
            f.write(f"Training Records: {len(X_train)}\n")
            f.write(f"Test Accuracy: {test_acc * 100:.1f}%\n")
            f.write(f"Test AUC: {test_auc:.3f}\n")
            f.write(f"Features: {', '.join(available_features)}\n")

        print(f"\n💾 Model saved to: {output_dir}/")

        # Create integration code
        create_integration_code(output_dir, available_features)

        return model, output_dir

    except ImportError:
        print("\n❌ XGBoost not installed!")
        print("Install with: pip install xgboost")
        return None, None


def create_integration_code(model_dir, features):
    """Create code to integrate ML with optimizer"""

    code = f'''#!/usr/bin/env python3
"""
ML INTEGRATION FOR DFS OPTIMIZER
================================
Use this to enhance your optimizer with ML predictions
"""

import pickle
import pandas as pd
import numpy as np
import os

class MLEnhancer:
    def __init__(self, model_dir="{model_dir}"):
        # Load model
        with open(os.path.join(model_dir, 'xgb_model.pkl'), 'rb') as f:
            self.model = pickle.load(f)

        self.features = {features}

    def enhance_players(self, players):
        """Enhance player projections with ML"""

        # Prepare features
        data = []
        for player in players:
            row = {{
                'salary': getattr(player, 'salary', 5000),
                'projection': getattr(player, 'base_projection', 10),
                'optimization_score': getattr(player, 'optimization_score', 10),
                'lineup_score': 0,  # Not available yet
                'lineup_rank': 50,  # Assume average
            }}

            # Add engineered features
            row['value_score'] = row['projection'] / (row['salary'] / 1000)
            row['rank_percentile'] = 0.5
            row['difficulty_numeric'] = 1  # Medium difficulty

            data.append(row)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Get predictions (probability of being in winning lineup)
        X = df[self.features].fillna(0)
        win_probabilities = self.model.predict_proba(X)[:, 1]

        # Apply adjustments
        for player, win_prob in zip(players, win_probabilities):
            # Boost players with high win probability
            if win_prob > 0.6:
                adjustment = 1.0 + (win_prob - 0.5) * 0.2  # Up to 20% boost
            else:
                adjustment = 1.0 - (0.5 - win_prob) * 0.1  # Up to 10% penalty

            # Apply to optimization score
            if hasattr(player, 'optimization_score'):
                player.optimization_score *= adjustment

            # Store ML score
            player.ml_win_probability = win_prob
            player.ml_adjustment = adjustment

        return players


# Usage example:
if __name__ == "__main__":
    from main_optimizer.unified_core_system import UnifiedCoreSystem

    # Load your system
    system = UnifiedCoreSystem()
    system.load_csv('DKSalaries.csv')

    # Enhance with ML
    enhancer = MLEnhancer()
    system.player_pool = enhancer.enhance_players(system.player_pool)

    # Now optimize with ML-enhanced scores
    lineups = system.optimize_lineups(
        num_lineups=20,
        strategy='projection_monster',  # Your best strategy
        contest_type='cash'
    )
'''

    integration_file = os.path.join(model_dir, 'ml_integration.py')
    with open(integration_file, 'w') as f:
        f.write(code)

    print(f"📝 Integration code saved: {integration_file}")


if __name__ == "__main__":
    import sys

    # Get CSV file
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Look for combined file
        import glob

        combined_files = glob.glob('ml_training_data_combined_*.csv')
        if combined_files:
            csv_file = max(combined_files)  # Get most recent
        else:
            print("❌ No combined CSV found!")
            print("Run combine_ml_data.py first")
            sys.exit(1)

    # Train model
    model, output_dir = train_ml_model(csv_file)

    if model:
        print("\n🎉 SUCCESS!")
        print(f"\n🚀 To use your ML model:")
        print(f"1. cd {output_dir}")
        print("2. python ml_integration.py")
        print("\nOr integrate into your optimizer:")
        print(f"from {output_dir}.ml_integration import MLEnhancer")