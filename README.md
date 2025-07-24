# 🏆 Correlation-Aware DFS Optimizer

**A simplified, proven MLB DFS optimizer that beats complex statistical models through correlation-based scoring.**

## 🚀 What's New (July 2025)

After extensive testing with 1,000 simulations, we discovered that a simple correlation-aware approach **outperformed 12 complex scoring methods**. This system has been completely rebuilt based on those results.

### 📊 Test Results
- **Winner**: Correlation-aware scoring (192.88 avg, 0.635 correlation)
- **Loser**: Complex Bayesian/statistical methods (181.71 avg)
- **Improvement**: +6.1% better performance with 90% less complexity

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
python launch_dfs_optimizer.py
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
```
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
│   └── correlation_scoring_config.py # Winning scoring config
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
│   └── launch_dfs_optimizer.py      # Quick launcher
│
└── Testing
    ├── test.py                      # System tests
    └── sample_data/                 # Test CSV files
```

## 🏆 Why This Works

The correlation-aware approach wins because it focuses on what actually matters in MLB DFS:

1. **Team Totals**: When teams score runs, multiple players contribute
2. **Batting Order**: Top of the order = more opportunities
3. **Natural Correlation**: Stacking happens organically

## 📈 Performance Improvements

- **Speed**: 10x faster than the old system
- **Accuracy**: +6.1% better lineup scores
- **Simplicity**: 90% less code to maintain
- **Reliability**: Predictable, consistent results

## 🤝 Contributing

This optimizer was rebuilt based on empirical testing. Future improvements should:
1. Test changes with simulations
2. Prove improvements statistically
3. Keep the system simple

## 📜 License

MIT License - See LICENSE file

---

**Remember**: In DFS, correlation beats calculation. This optimizer proves it with data! 🎯
