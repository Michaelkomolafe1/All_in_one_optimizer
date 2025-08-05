#!/usr/bin/env python3
"""
FIXED SLATE-AWARE ML TRAINER
============================
Standalone version - no import errors!
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
import os
import warnings
import json

warnings.filterwarnings('ignore')


def analyze_and_train(csv_file="ml_training_data_combined_20250805_025325.csv"):
    """Analyze CSV and train ML model in one go"""

    print("🤖 SLATE-AWARE ML TRAINER")
    print("=" * 60)

    # First, analyze the CSV structure
    print("\n📊 ANALYZING YOUR DATA...")
    print("-" * 40)

    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df):,} records from {csv_file}")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        print("\nMake sure you have run combine_ml_data.py first!")
        return None, None

    # Show columns
    print(f"\n📋 Columns found ({len(df.columns)} total):")
    for i, col in enumerate(df.columns[:20]):  # Show first 20
        print(f"   {i + 1:2d}. {col}")
    if len(df.columns) > 20:
        print(f"   ... and {len(df.columns) - 20} more")

    # Check critical columns
    print("\n🔍 Checking critical columns:")
    critical_cols = ['slate_size', 'contest_type', 'strategy', 'lineup_win', 'salary', 'projection']
    for col in critical_cols:
        if col in df.columns:
            print(f"   ✓ {col}")
        else:
            print(f"   ✗ {col} - MISSING!")

    # Analyze distributions
    if 'slate_size' in df.columns:
        print(f"\n📏 Slate Size Distribution:")
        for size, count in df['slate_size'].value_counts().items():
            print(f"   {size:8s}: {count:,} records")

    if 'contest_type' in df.columns:
        print(f"\n🎯 Contest Type Distribution:")
        for ctype, count in df['contest_type'].value_counts().items():
            print(f"   {ctype:8s}: {count:,} records")

    if 'strategy' in df.columns:
        print(f"\n🎮 Strategy Distribution:")
        for strat, count in df['strategy'].value_counts().head(10).items():
            print(f"   {strat:30s}: {count:,} records")

    if 'difficulty_level' in df.columns:
        print(f"\n🎚️ Difficulty Distribution:")
        for diff, count in df['difficulty_level'].value_counts().items():
            win_rate = df[df['difficulty_level'] == diff]['lineup_win'].mean() * 100
            print(f"   {diff:8s}: {count:,} records ({win_rate:.1f}% win rate)")

    # Check for slate_size - CRITICAL!
    if 'slate_size' not in df.columns:
        print("\n⚠️  WARNING: No slate_size column found!")
        print("   Will use default 'medium' for all records")
        df['slate_size'] = 'medium'

    # Now train the model
    print("\n" + "=" * 60)
    print("🚀 TRAINING ML MODEL")
    print("=" * 60)

    # Feature engineering
    print("\n🔧 Creating features...")

    features = []

    # Basic numeric features
    if 'salary' in df.columns:
        df['salary'] = pd.to_numeric(df['salary'], errors='coerce').fillna(5000)
        features.append('salary')

    if 'projection' in df.columns:
        df['projection'] = pd.to_numeric(df['projection'], errors='coerce').fillna(10)
        features.append('projection')

    if 'optimization_score' in df.columns:
        df['optimization_score'] = pd.to_numeric(df['optimization_score'], errors='coerce').fillna(10)
        features.append('optimization_score')

    # Create value score
    if 'salary' in features and 'projection' in features:
        df['value_score'] = df['projection'] / (df['salary'] / 1000)
        df['value_score'] = df['value_score'].replace([np.inf, -np.inf], 0).fillna(0)
        features.append('value_score')

    # Encode slate size
    slate_map = {'small': 0, 'medium': 1, 'large': 2}
    df['slate_size_encoded'] = df['slate_size'].map(slate_map).fillna(1)
    features.append('slate_size_encoded')

    # Encode contest type
    df['is_cash'] = (df['contest_type'] == 'cash').astype(int)
    features.append('is_cash')

    # Strategy effectiveness mapping
    print("\n📊 Computing strategy effectiveness...")

    # Calculate actual win rates by strategy/slate/contest
    strategy_effectiveness = {}
    if all(col in df.columns for col in ['strategy', 'slate_size', 'contest_type', 'lineup_win']):
        for strategy in df['strategy'].unique():
            for slate_size in df['slate_size'].unique():
                for contest_type in df['contest_type'].unique():
                    mask = (df['strategy'] == strategy) & \
                           (df['slate_size'] == slate_size) & \
                           (df['contest_type'] == contest_type)
                    if mask.sum() > 10:  # Need enough samples
                        win_rate = df[mask]['lineup_win'].mean()
                        key = f"{strategy}_{slate_size}_{contest_type}"
                        strategy_effectiveness[key] = 1.0 + (win_rate - 0.3) * 0.5

    # Apply strategy effectiveness
    df['strategy_fit'] = df.apply(
        lambda row: strategy_effectiveness.get(
            f"{row.get('strategy', 'unknown')}_{row.get('slate_size', 'medium')}_{row.get('contest_type', 'gpp')}",
            1.0
        ), axis=1
    )
    features.append('strategy_fit')

    # Add difficulty if available
    if 'difficulty_level' in df.columns:
        diff_map = {'easy': 0, 'medium': 1, 'hard': 2, 'extreme': 3}
        df['difficulty_encoded'] = df['difficulty_level'].map(diff_map).fillna(1)
        features.append('difficulty_encoded')

    # Prepare for training
    print(f"\n📊 Final feature set: {features}")

    X = df[features].fillna(0)
    y = df['lineup_win'].astype(int)

    print(f"\n📈 Dataset summary:")
    print(f"   Total samples: {len(X):,}")
    print(f"   Features: {len(features)}")
    print(f"   Win rate: {y.mean() * 100:.1f}%")

    # Train XGBoost
    try:
        import xgboost as xgb
        print("\n✅ XGBoost imported successfully")
    except ImportError:
        print("\n❌ XGBoost not installed!")
        print("Install with: pip install xgboost")
        return None, None

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n🏋️ Training model...")
    print(f"   Train size: {len(X_train):,}")
    print(f"   Test size: {len(X_test):,}")

    # Create and train model - handle different XGBoost versions
    try:
        # Try newer API first
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            scale_pos_weight=(1 - y_train).sum() / y_train.sum() if y_train.sum() > 0 else 1,
            eval_metric='logloss'
        )

        # Fit without early stopping
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
    except Exception as e:
        print(f"⚠️  First attempt failed: {e}")
        print("   Trying alternative approach...")

        # Fallback to simpler approach
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

        model.fit(X_train, y_train, verbose=False)

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_proba)

    print(f"\n📊 Model Performance:")
    print(f"   Accuracy: {accuracy * 100:.1f}%")
    print(f"   AUC: {auc:.3f}")

    # Feature importance
    print(f"\n🎯 Feature Importance:")
    importance_df = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for _, row in importance_df.iterrows():
        bar_length = int(row['importance'] * 50)
        bar = '█' * bar_length
        print(f"   {row['feature']:20s} {bar} {row['importance']:.3f}")

    # Save model
    output_dir = f"ml_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    # Save model
    with open(os.path.join(output_dir, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)

    # Save metadata
    metadata = {
        'features': features,
        'accuracy': float(accuracy),
        'auc': float(auc),
        'training_date': datetime.now().isoformat(),
        'training_samples': len(X_train),
        'slate_sizes': df['slate_size'].value_counts().to_dict() if 'slate_size' in df.columns else {},
        'strategy_effectiveness': strategy_effectiveness
    }

    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Model saved to: {output_dir}/")

    # Create integration script
    create_integration_script(output_dir, features, metadata)

    return model, output_dir


def create_integration_script(output_dir, features, metadata):
    """Create a simple integration script"""

    code = f'''#!/usr/bin/env python3
"""
ML OPTIMIZER INTEGRATION
========================
"""

import pickle
import pandas as pd
import numpy as np
import os

class MLOptimizer:
    def __init__(self, model_dir="{output_dir}"):
        with open(os.path.join(model_dir, 'model.pkl'), 'rb') as f:
            self.model = pickle.load(f)
        self.features = {features}

    def enhance_players(self, players, slate_size='medium', contest_type='gpp'):
        """Enhance player scores with ML predictions"""

        # Prepare data
        data = []
        for p in players:
            row = {{
                'salary': getattr(p, 'salary', 5000),
                'projection': getattr(p, 'base_projection', 10),
                'optimization_score': getattr(p, 'optimization_score', 10),
                'value_score': 0,  # Calculate below
                'slate_size_encoded': {{'small': 0, 'medium': 1, 'large': 2}}.get(slate_size, 1),
                'is_cash': 1 if contest_type == 'cash' else 0,
                'strategy_fit': 1.0,
                'difficulty_encoded': 1  # Medium
            }}

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
# from {output_dir}.integration import MLOptimizer
# ml = MLOptimizer()
# enhanced_players = ml.enhance_players(players, slate_size='medium', contest_type='gpp')
'''

    with open(os.path.join(output_dir, 'integration.py'), 'w') as f:
        f.write(code)

    print(f"📝 Integration script created: {output_dir}/integration.py")


if __name__ == "__main__":
    import sys

    # Get CSV file from command line or use default
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Try to find the combined CSV
        import glob

        combined_files = glob.glob('ml_training_data_combined_*.csv')
        if combined_files:
            csv_file = max(combined_files)  # Most recent
            print(f"📂 Found combined CSV: {csv_file}")
        else:
            print("❌ No combined CSV found!")
            print("\nPlease run combine_ml_data.py first, or specify a CSV file:")
            print("python fixed_slate_ml_trainer.py your_file.csv")
            sys.exit(1)

    # Train model
    model, output_dir = analyze_and_train(csv_file)

    if model:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! ML MODEL TRAINED")
        print("=" * 60)

        print("\n📚 HOW TO USE YOUR MODEL:")
        print("\n1. In your optimizer, add:")
        print(f"   from {output_dir}.integration import MLOptimizer")
        print("   ml = MLOptimizer()")
        print("   players = ml.enhance_players(players, slate_size='medium', contest_type='gpp')")

        print("\n2. The model will:")
        print("   • Predict win probability for each player")
        print("   • Boost high-probability players (up to +20%)")
        print("   • Slightly penalize low-probability players (-5%)")

        print("\n3. Your strategies still control lineup building")
        print("   The ML just enhances the player scores!")