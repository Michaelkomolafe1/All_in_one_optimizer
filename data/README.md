# DFS Optimizer - Professional MLB Lineup Optimizer

## Overview
A sophisticated Daily Fantasy Sports optimizer that combines real-time MLB data, advanced statistical modeling, and machine learning-optimized scoring parameters to generate winning lineups for DraftKings contests.

## Key Features
- **Auto Contest Detection**: Automatically identifies Classic vs Showdown slates
- **Real-Time Data Integration**: 
  - Live MLB confirmed lineups via Smart Confirmation System
  - Statcast advanced metrics (barrel rates, xwOBA, recent form)
  - Vegas betting lines and team totals
  - Ownership projections
- **Contest-Specific Optimization**:
  - **GPP** (Tournaments): -67.7 score optimization emphasizing ceiling/stacks
  - **Cash** (50/50s): 86.2 score optimization emphasizing floor/consistency
- **Smart Player Pool Management**: Confirmed starters + manual selections
- **Professional GUI**: Full-featured interface with real-time updates

## Project Structure
```
All_in_one_optimizer/
├── core/
│   ├── dfs_optimizer_integrated.py    # Main GUI application
│   ├── launch_optimizer.py            # Application launcher
│   ├── complete_dfs_system_integrated.py  # Original integrated system
│   └── unified_milp_optimizer.py     # MILP optimization engine
├── data/
│   ├── smart_confirmation_system.py   # MLB lineup confirmations
│   ├── simple_statcast_fetcher.py     # Baseball Savant data
│   ├── vegas_lines.py                 # Betting lines & totals
│   ├── ownership_calculator.py        # Ownership projections
│   └── ownership_wrapper.py           # Import helper
└── enhanced_scoring_engine.py         # Optimized scoring parameters
```

## How It Works

### 1. **Data Loading**
- Load DraftKings CSV → Auto-detects Classic (P/C/1B/2B/3B/SS/OF) or Showdown (CPT/UTIL)
- Showdown: Automatically filters CPT duplicates, uses UTIL entries only

### 2. **Player Confirmation**
- Fetches real MLB confirmed lineups from MLB API
- Marks confirmed pitchers and position players
- Tracks batting order for confirmed hitters

### 3. **Pool Building**
- **Confirmed Only**: Filters to only confirmed MLB starters
- **Manual Selection**: Add any players via checkboxes
- Creates optimized player pool for contest type

### 4. **Data Enhancement**
**Cash Contest Enhancement:**
- Recent performance (last 4-5 games) - 37% weight
- Consistency scores & floor projections - 80% weight
- Platoon advantages (+8.4% when favorable)
- Pitcher matchup quality

**GPP Contest Enhancement:**
- Ownership projections (<15% get +10.6% boost)
- Team totals (>5.73 runs get +33.6% boost)  
- Barrel rates (>11.7% get +19.4% boost)
- Stack correlation bonuses

### 5. **Optimization**
Uses MILP (Mixed Integer Linear Programming) with:
- **GPP**: 4-player stacks, max 5 per team, ownership leverage
- **Cash**: Max 3 per team, consistency focus, high floor

## Optimized Parameters

### GPP (Score: -67.7)
- Preferred stack size: 4 players
- Batting order boost: +11.5% for top 5
- Low ownership boost: +10.6% if <15%
- High team total mult: 1.336x

### Cash (Score: 86.2)  
- Projection weight: 37.7%
- Recent form weight: 36.9%
- Floor weight: 80%
- Platoon advantage: +8.4%

## Usage

### Starting the Optimizer
```bash
cd /home/michael/Desktop/All_in_one_optimizer
python3 core/launch_optimizer.py
```

### Workflow
1. **Load CSV** → Select your DraftKings CSV file
2. **Fetch Confirmations** → Get real MLB confirmed lineups
3. **Select Contest** → Choose GPP or Cash
4. **Build Pool** → Filter players (confirmed + manual)
5. **Set Lineups** → Choose 1-150 lineups
6. **Optimize** → Generate optimal lineups
7. **Export** → Save lineups for DraftKings upload

## Technical Stack
- **GUI**: PyQt5 
- **Data Processing**: Pandas, NumPy
- **Optimization**: PuLP (MILP solver)
- **APIs**: MLB Stats API, Baseball Savant
- **ML Parameters**: Optimized via Gradient Descent

## What Makes It Special
This isn't a generic optimizer - it uses machine learning optimized parameters specifically tuned for DFS success:
- **GPP parameters** optimized to score -67.7 (64th percentile lineups)
- **Cash parameters** optimized to score 86.2 (79% win rate)
- Real-time data integration ensures you're using actual confirmed starters
- Contest-specific player enhancement means different data for different contest types

## Quick Tips
- **For Cash**: Always use "Confirmed Only" for safety
- **For GPP**: Add manual selections for differentiation  
- **Refresh confirmations** closer to lock for late scratches
- **Export and review** lineups before uploading to DraftKings

---
*Built with comprehensive data integration and machine learning optimization for serious DFS players*