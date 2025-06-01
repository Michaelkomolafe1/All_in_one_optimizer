# 🚀 Enhanced DFS Optimizer

## Quick Start (3 commands)

```bash
# 1. Test the system
python launch_enhanced_dfs.py test

# 2. Launch GUI  
python launch_enhanced_dfs.py

# 3. Edit settings (optional)
# Edit dfs_settings.py to customize
```

## New Features Added ✨

✅ **Vegas Lines Integration** - Real sportsbook data for team context  
✅ **Team Stacking** - Smart 2-4 player stacks for cash games  
✅ **Enhanced Statcast** - Percentile-based analysis vs raw stats  
✅ **Multi-Position MILP** - Handles Jorge Polanco (3B/SS) correctly  
✅ **Manual Selection Priority** - Your picks get priority scoring  

## Settings

### Cash Games (Recommended)
- Strategy: "Smart Default"
- Stacking: 2-3 players max  
- Focus: Consistent, high-floor players

### Tournaments
- Strategy: "Smart Default" or "All Players"
- Stacking: 3-4 players max
- Focus: Upside and contrarian plays

## Files Created
- `launch_enhanced_dfs.py` - Main launcher
- `dfs_settings.py` - Configuration  
- `README.md` - This guide

## Troubleshooting

**Import Errors**: Run `pip install pandas numpy pulp requests PyQt5`

**No Vegas Data**: Check internet connection (updates every 2 hours)

**No Stacks**: Normal behavior - diversification is often optimal

## Support
- Test mode: `python launch_enhanced_dfs.py test`
- All original features preserved
- Backwards compatible with existing workflows

---
*Enhanced DFS System - Auto-configured*
