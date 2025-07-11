# DFS Optimizer - Clean Version

## 🚀 Quick Start

1. **Launch the GUI:**
   ```bash
   python launch_optimizer.py
   # or
   python enhanced_dfs_gui.py
   ```

2. **Load your CSV file** (DraftKings format)

3. **Select optimization strategy** and generate lineups!

## 📁 Project Structure

```
DFS_Optimizer/
├── launch_optimizer.py          # Main launcher
├── enhanced_dfs_gui.py          # GUI interface
├── bulletproof_dfs_core.py      # Core optimizer
├── unified_player_model.py      # Player data model
├── vegas_lines.py               # Vegas data integration
├── simple_statcast_fetcher.py   # Baseball stats
├── utils/                       # Utility modules
├── sample_data/                 # Sample CSV files
├── archive/                     # Archived old files
└── docs/                        # Documentation
```

## 🎯 Features

- ✅ Multi-position player support
- ✅ Manual player selection
- ✅ Multiple optimization strategies
- ✅ Real-time data integration
- ✅ Professional GUI interface

## 📊 Optimization Strategies

1. **Balanced** - Mix of ceiling and floor
2. **Ceiling** - Maximum upside
3. **Safe** - Consistent floor plays
4. **Value** - Best points per dollar
5. **Contrarian** - Low ownership GPP plays

## 🔧 Requirements

See `requirements.txt` for Python dependencies.

## 💡 Tips

- Use sample_data/DKSalaries_test.csv for testing
- Check archive/ folder for old versions if needed
- Output lineups are saved to output/ folder

Last updated: Fri Jul 11 03:09:26 AM EDT 2025
