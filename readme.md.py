# 🏆 Correlation-Aware DFS Optimizer

**A simplified, proven MLB DFS optimizer that beats complex statistical models through correlation-based scoring.**

## 🚀 What's New (July 2025)

After extensive testing with 1,000 simulations, we discovered that a simple correlation-aware approach **outperformed 12 complex scoring methods**. This system has been completely rebuilt based on those results.

### 📊 Test Results
- **Winner**: Correlation-aware scoring (192.88 avg, 0.635 correlation)
- **Loser**: Complex Bayesian/statistical methods (181.71 avg)
- **Improvement**: +6.1% better performance with 90% less complexity

### 🎯 Key Changes

**BEFORE (Complex System):**
- 12 different scoring methods
- Complex weight redistribution
- Multiple scoring engines
- Unpredictable results
- Slow performance

**AFTER (Correlation-Aware):**
- 1 simple scoring method
- Clear multipliers (1.15x for high-scoring teams, 1.10x for top batting order)
- Natural stacking correlation
- Fast, predictable results
- Proven winner in testing

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/All_in_one_optimizer.git
cd All_in_one_optimizer
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## 🎮 Quick Start

### GUI Mode (Recommended)
```bash
python complete_dfs_gui_debug.py
```

### Command Line
```bash
python unified_core_system.py --csv your_slate.csv --contest gpp --lineups 20
```

### Test the System
```bash
python test.py
```

## 📋 How It Works

### The Winning Formula
```python
Score = Base Projection × Team Boost × Order Boost

Where:
- Team Boost = 1.15 if team total > 5 runs (GPP) or 1.08 (Cash)
- Order Boost = 1.10 if batting 1-4 (GPP) or 1.05 (Cash)
```

### Contest Modes

**GPP Mode (Tournaments):**
- Aggressive stacking (3-5 players)
- Full correlation bonuses
- High variance plays

**Cash Mode (50/50s):**
- Conservative approach (2-3 players max)
- Reduced bonuses
- Consistency focus

## 📁 Project Structure

```
All_in_one_optimizer/
├── Core Files
│   ├── unified_core_system.py       # Main system orchestrator
│   ├── unified_player_model.py      # Player data model
│   ├── unified_milp_optimizer.py    # MILP optimization engine
│   └── correlation_scoring_config.py # NEW: Winning scoring config
│
├── New Scoring System
│   ├── step2_updated_player_model.py # Simplified scoring engine
│   └── step3_stack_detection.py      # Smart stack detection
│
├── Data Sources
│   ├── smart_confirmation_system.py  # Starting lineups
│   ├── simple_statcast_fetcher.py   # Player stats
│   ├── vegas_lines.py               # Betting lines
│   └── weather_integration.py       # Weather data
│
├── User Interface
│   ├── complete_dfs_gui_debug.py    # GUI interface
│   └── launch_optimizer.py          # Quick launcher
│
└── Testing
    ├── test.py                      # System tests
    └── sample_data/                 # Test CSV files
```

## 🔧 Configuration

### Scoring Configuration (`correlation_scoring_config.py`)
```python
# GPP Settings (Default)
team_total_threshold = 5.0  # Teams scoring 5+ runs get boost
team_total_boost = 1.15     # 15% boost
batting_order_boost = 1.10  # 10% boost for top 4

# Cash Settings (Conservative)
team_total_boost = 1.08     # 8% boost (reduced)
batting_order_boost = 1.05  # 5% boost (reduced)
```

## 📊 Usage Examples

### Basic GPP Optimization
```python
from unified_core_system import UnifiedCoreSystem

# Initialize
system = UnifiedCoreSystem()

# Load players
system.load_players_from_csv("DKSalaries.csv")

# Set confirmed players
system.set_confirmed_players(confirmed_list)

# Enrich data
system.enrich_player_pool()

# Generate lineups
lineups = system.optimize_lineups(
    num_lineups=20,
    contest_type="gpp"  # Aggressive stacking
)
```

### Cash Game Optimization
```python
# Same setup, different contest type
lineups = system.optimize_lineups(
    num_lineups=3,
    contest_type="cash"  # Conservative mode
)
```

## 🏆 Why This Works

The correlation-aware approach wins because it focuses on what actually matters in MLB DFS:

1. **Team Totals**: When teams score runs, multiple players contribute
2. **Batting Order**: Top of the order = more opportunities
3. **Natural Correlation**: Stacking happens organically

Instead of trying to predict individual performance with complex statistics, we identify which game environments produce fantasy points.

## 📈 Performance Improvements

- **Speed**: 10x faster than the old system
- **Accuracy**: +6.1% better lineup scores
- **Simplicity**: 90% less code to maintain
- **Reliability**: Predictable, consistent results

## 🐛 Troubleshooting

### Import Errors
Make sure all Step files are in your project directory:
- `correlation_scoring_config.py`
- `step2_updated_player_model.py`
- `step3_stack_detection.py`

### Missing Players
The system only uses confirmed players. Check:
1. CSV loaded correctly
2. Confirmations fetched
3. Player pool built

### Low Scores
Verify contest type is set correctly:
- GPP = Higher scores, more variance
- Cash = Lower scores, more consistency

## 🤝 Contributing

This optimizer was rebuilt based on empirical testing. Future improvements should:
1. Test changes with simulations
2. Prove improvements statistically
3. Keep the system simple

## 📜 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Built through extensive testing and iteration. Special thanks to the DFS community for insights on correlation-based strategies.

---

**Remember**: In DFS, correlation beats calculation. This optimizer proves it with data! 🎯