#!/usr/bin/env python3
"""
SIMPLIFIED ML WORKFLOW
======================
Leverages your existing tools to create an ML-enhanced optimizer
"""

import os
import sys
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing as mp
from typing import Dict, List, Any

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import YOUR existing tools
from simulation.parameter_optimization_framework import ParameterOptimizer
from simulation.realistic_ml_competition import RealisticMLCompetition
from simulation.parallel_ml_bridge import ParallelYourSystemMLBridge
from simulation.bayesian_parameter_optimizer import BayesianParameterOptimizer


class SimplifiedMLWorkflow:
    """
    Simplified workflow that actually uses your existing tools
    """

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or f"ml_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = {}

    def run_workflow(self, difficulty='medium', quick_mode=False):
        """
        Execute simplified ML workflow

        Steps:
        1. Find optimal parameters (Bayesian or Grid)
        2. Generate REAL training data using those parameters
        3. Train simple ML model on the data
        4. Create integration code
        """

        print("""
        🚀 SIMPLIFIED ML WORKFLOW
        ========================

        This workflow will:
        1. ✅ Find optimal parameters (30 min)
        2. ✅ Generate real training data (20 min)
        3. ✅ Train simple ML model (5 min)
        4. ✅ Create integration code

        Total time: ~55 minutes
        """)

        confirm = input("\nProceed? (y/n): ")
        if confirm.lower() != 'y':
            return

        start_time = time.time()

        # Step 1: Optimize Parameters
        print("\n" + "=" * 60)
        print("STEP 1: PARAMETER OPTIMIZATION")
        print("=" * 60)

        if quick_mode:
            print("Using quick grid search...")
            optimal_params = self.quick_parameter_optimization()
        else:
            print("Using Bayesian optimization...")
            optimal_params = self.bayesian_parameter_optimization()

        # Step 2: Generate Training Data
        print("\n" + "=" * 60)
        print("STEP 2: GENERATE REAL TRAINING DATA")
        print("=" * 60)

        training_data = self.generate_real_training_data(optimal_params, difficulty)

        # Step 3: Train ML Model
        print("\n" + "=" * 60)
        print("STEP 3: TRAIN ML MODEL")
        print("=" * 60)

        ml_model = self.train_simple_ml_model(training_data)

        # Step 4: Create Integration
        print("\n" + "=" * 60)
        print("STEP 4: CREATE INTEGRATION")
        print("=" * 60)

        self.create_ml_integration(ml_model, optimal_params)

        # Summary
        total_time = time.time() - start_time
        self.print_summary(total_time)

        return self.results

    def bayesian_parameter_optimization(self):
        """Use Bayesian optimization for YOUR strategies"""

        # Create custom Bayesian optimizer for your strategies
        from skopt import gp_minimize
        from skopt.space import Real, Integer

        print("\n🔧 Optimizing key strategies with Bayesian approach...")

        optimal_params = {}

        # Define search spaces for YOUR strategies
        search_spaces = {
            'projection_monster': [
                Real(0.0, 1.5, name='park_weight'),
                Real(0.0, 1.0, name='value_bonus_weight'),
                Integer(6, 12, name='min_projection_threshold')
            ],
            'truly_smart_stack': [
                Real(0.15, 0.35, name='projection_weight'),
                Real(0.15, 0.35, name='ceiling_weight'),
                Real(0.15, 0.35, name='matchup_weight'),
                Real(0.15, 0.35, name='game_total_weight'),
                Integer(3, 5, name='min_stack_size'),
                Real(4.0, 5.5, name='bad_pitcher_era')
            ]
        }

        for strategy, space in search_spaces.items():
            print(f"\n  Optimizing {strategy}...")

            # Objective function
            def objective(params):
                # Test these parameters
                param_dict = {dim.name: val for dim, val in zip(space, params)}

                # Quick test with parallel ML bridge
                bridge = ParallelYourSystemMLBridge(num_cores=4)

                # Test on 10 slates
                results = []
                for i in range(10):
                    slate_result = bridge.process_single_slate((
                        i * 1000,
                        {'strategy': strategy, 'params': param_dict},
                        'gpp' if 'stack' in strategy else 'cash',
                        'medium'
                    ))
                    if slate_result:
                        results.append(slate_result)

                # Calculate performance
                if results:
                    avg_roi = np.mean([r.get('roi', -100) for r in results])
                    return -avg_roi  # Minimize negative ROI
                return 100  # Penalty for failure

            # Run optimization
            result = gp_minimize(
                func=objective,
                dimensions=space,
                n_calls=25,  # Quick optimization
                n_initial_points=10,
                random_state=42
            )

            # Extract optimal parameters
            optimal_params[strategy] = {
                dim.name: val for dim, val in zip(space, result.x)
            }

            print(f"  ✅ Best ROI: {-result.fun:.1f}%")

        # Save parameters
        with open(os.path.join(self.output_dir, 'optimal_params.json'), 'w') as f:
            json.dump(optimal_params, f, indent=2)

        self.results['optimal_params'] = optimal_params
        return optimal_params

    def quick_parameter_optimization(self):
        """Quick grid search for testing"""

        print("\n🔧 Quick parameter optimization...")

        # Use existing parameter optimizer
        optimizer = ParameterOptimizer(num_cores=mp.cpu_count())

        # Test key strategies with fewer slates
        results = optimizer.optimize_strategy(
            'projection_monster', 'cash', 'medium', slates_per_config=10
        )

        optimal_params = {
            'projection_monster': results['params'] if results else {}
        }

        self.results['optimal_params'] = optimal_params
        return optimal_params

    def generate_real_training_data(self, optimal_params: Dict, difficulty: str):
        """Generate REAL training data using competition"""

        print(f"\n📊 Generating training data with {difficulty} difficulty...")

        # Use RealisticMLCompetition with specified difficulty
        competition = RealisticMLCompetition(
            num_cores=mp.cpu_count(),
            difficulty=difficulty
        )

        # Run competition to generate real data
        print("\n  Running realistic competition...")
        competition_results = competition.run_competition(
            slates_per_config=50 if difficulty != 'extreme' else 25
        )

        # The competition already saves the CSV, but let's also load it
        # Find the most recent file
        import glob
        pattern = f"ml_training_data_{difficulty}_*.csv"
        files = glob.glob(pattern)

        if files:
            latest_file = max(files, key=os.path.getctime)
            df = pd.read_csv(latest_file)

            # Copy to our output directory
            import shutil
            new_path = os.path.join(self.output_dir, 'training_data.csv')
            shutil.copy(latest_file, new_path)

            print(f"\n  ✅ Generated {len(df):,} training records")
            print(f"  💾 Saved to: {new_path}")

            self.results['training_data'] = df
            return df
        else:
            print("  ❌ No training data generated!")
            return pd.DataFrame()

    def train_simple_ml_model(self, training_data: pd.DataFrame):
        """Train a simple XGBoost model"""

        if training_data.empty:
            print("  ⚠️  No training data available!")
            return None

        print("\n🤖 Training ML model...")

        try:
            import xgboost as xgb
        except ImportError:
            print("  ❌ XGBoost not installed! Run: pip install xgboost")
            return None

        # Prepare features
        feature_cols = [
            'salary', 'projection', 'optimization_score',
            'lineup_score', 'field_avg_score'
        ]

        # Only use available columns
        available_features = [col for col in feature_cols if col in training_data.columns]

        if len(available_features) < 3:
            print("  ⚠️  Not enough features available!")
            return None

        X = training_data[available_features]

        # Target: Did player exceed projection?
        y = training_data['actual_score'] - training_data['projection']

        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train model
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Evaluate
        from sklearn.metrics import mean_absolute_error
        train_mae = mean_absolute_error(y_train, model.predict(X_train))
        test_mae = mean_absolute_error(y_test, model.predict(X_test))

        print(f"  ✅ Model trained!")
        print(f"     Train MAE: {train_mae:.2f}")
        print(f"     Test MAE: {test_mae:.2f}")

        # Save model
        import pickle
        model_path = os.path.join(self.output_dir, 'ml_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        print(f"  💾 Model saved to: {model_path}")

        self.results['ml_model'] = model
        return model

    def create_ml_integration(self, ml_model, optimal_params):
        """Create integration code"""

        integration_code = '''#!/usr/bin/env python3
"""
ML-ENHANCED DFS OPTIMIZER
========================
Simple integration of ML predictions with your optimizer
"""

import pickle
import pandas as pd
import numpy as np
from typing import List

class MLEnhancedOptimizer:
    """Simple ML enhancement for your optimizer"""

    def __init__(self, model_path: str):
        """Load the trained model"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def enhance_projections(self, players: List) -> List:
        """
        Adjust player projections based on ML predictions

        The model predicts: actual_score - projection
        So we add this to the base projection
        """

        # Prepare features
        features = []
        for player in players:
            # Use available attributes
            feature_dict = {
                'salary': getattr(player, 'salary', 5000),
                'projection': getattr(player, 'base_projection', 10),
                'optimization_score': getattr(player, 'optimization_score', 10),
                'lineup_score': 0,  # Not available yet
                'field_avg_score': 150  # Typical average
            }
            features.append(feature_dict)

        # Create DataFrame
        feature_df = pd.DataFrame(features)

        # Get predictions (expected delta from projection)
        try:
            deltas = self.model.predict(feature_df)
        except:
            # If prediction fails, return unchanged
            return players

        # Apply adjustments
        for player, delta in zip(players, deltas):
            # Adjust projection by predicted delta
            # But cap adjustments at +/- 20%
            max_adjustment = player.base_projection * 0.2
            capped_delta = np.clip(delta, -max_adjustment, max_adjustment)

            # Create new projection
            player.ml_projection = player.base_projection + capped_delta

            # Update optimization score to use ML projection
            # This preserves your strategy logic while using better projections
            ratio = player.ml_projection / player.base_projection
            player.optimization_score *= ratio

        return players


# Integration with your system:
def integrate_with_optimizer():
    """Example of how to use with your optimizer"""

    from main_optimizer.unified_core_system import UnifiedCoreSystem

    # Load your system
    system = UnifiedCoreSystem()
    system.load_csv('DKSalaries.csv')

    # Enhance with ML
    ml_enhancer = MLEnhancedOptimizer('ml_model.pkl')
    system.players = ml_enhancer.enhance_projections(system.players)

    # Now optimize as normal - your strategies still work!
    lineups = system.optimize_lineups(
        num_lineups=20,
        strategy='truly_smart_stack',
        contest_type='gpp'
    )

    return lineups
'''

        # Save integration code
        integration_path = os.path.join(self.output_dir, 'ml_integration.py')
        with open(integration_path, 'w') as f:
            f.write(integration_code)

        print(f"\n💾 Integration code saved to: {integration_path}")

        # Also save optimal parameters as Python module
        param_code = f'''# Optimal parameters from ML workflow
OPTIMAL_PARAMS = {json.dumps(optimal_params, indent=4)}
'''

        param_path = os.path.join(self.output_dir, 'optimal_params.py')
        with open(param_path, 'w') as f:
            f.write(param_code)

        print(f"💾 Parameters saved to: {param_path}")

    def print_summary(self, total_time: float):
        """Print workflow summary"""

        print("\n" + "=" * 60)
        print("🎉 WORKFLOW COMPLETE!")
        print("=" * 60)

        print(f"\nTotal time: {total_time / 60:.1f} minutes")
        print(f"Output directory: {self.output_dir}/")

        print("\n📁 Generated files:")
        for file in os.listdir(self.output_dir):
            size = os.path.getsize(os.path.join(self.output_dir, file)) / 1024
            print(f"  • {file} ({size:.1f} KB)")

        print("\n🚀 NEXT STEPS:")
        print("1. Review the training data quality")
        print("2. Test the ML model predictions")
        print("3. Run backtests with and without ML")
        print("4. Deploy if performance improves!")

        print("\n💡 Key insight: ML should enhance, not replace your strategies!")


if __name__ == "__main__":
    print("""
    🚀 SIMPLIFIED ML WORKFLOW
    ========================

    This uses YOUR existing tools:
    • Parameter optimization (Grid or Bayesian)
    • Realistic competition for training data
    • Simple ML model for projection adjustment
    • Easy integration with your optimizer

    Difficulty options:
    1. Easy - Mixed field, good for initial testing
    2. Medium - Balanced competition (recommended)
    3. Hard - Tough field, fewer weak players
    4. Extreme - Almost all sharks
    5. Sliding - Starts easy, gets harder
    """)

    # Get difficulty choice
    diff_choice = input("\nSelect difficulty (1-5): ")
    difficulty_map = {
        '1': 'easy',
        '2': 'medium',
        '3': 'hard',
        '4': 'extreme',
        '5': 'sliding'
    }
    difficulty = difficulty_map.get(diff_choice, 'medium')

    # Quick mode?
    quick = input("\nUse quick mode? (fewer tests, ~20 min) (y/n): ")
    quick_mode = quick.lower() == 'y'

    # Run workflow
    workflow = SimplifiedMLWorkflow()
    results = workflow.run_workflow(difficulty=difficulty, quick_mode=quick_mode)

    print("\n✅ Workflow complete!")