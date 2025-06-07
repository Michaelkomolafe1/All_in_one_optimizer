# DFS System Integration Guide
# =============================

## 1. CORE INTEGRATION (bulletproof_dfs_core.py)

### Add imports at the top:
```python
# Add after your existing imports
try:
    from smart_cache import smart_cache
    from multi_lineup_optimizer import MultiLineupOptimizer
    from performance_tracker import tracker
    UPGRADES_AVAILABLE = True
except ImportError:
    print("⚠️ Optional upgrades not installed")
    UPGRADES_AVAILABLE = False
```

### Add these methods to BulletproofDFSCore class:

```python
def get_cached_data(self, key: str, fetch_func, category: str = 'default'):
    """Use smart caching for any data fetch"""
    if UPGRADES_AVAILABLE:
        return smart_cache.get_or_fetch(key, fetch_func, category)
    else:
        return fetch_func()

def generate_multiple_lineups(self, count: int = 20) -> List:
    """Generate multiple unique lineups"""
    if not UPGRADES_AVAILABLE:
        print("Multi-lineup module not available")
        return []

    optimizer = MultiLineupOptimizer(self)
    lineups = optimizer.generate_gpp_lineups(
        num_lineups=count,
        max_exposure=0.5,
        min_salary=49000
    )

    # Show summary
    optimizer.print_summary()

    # Export for upload
    optimizer.export_for_upload('draftkings')

    return lineups

def track_lineup_performance(self, lineup: List, contest_info: Dict):
    """Track lineup for future analysis"""
    if not UPGRADES_AVAILABLE:
        return

    return tracker.log_contest(lineup, contest_info)
```

### Update existing methods to use caching:

In `detect_confirmed_players` method, wrap the API call:
```python
# OLD:
lineup_count, pitcher_count = self.confirmation_system.get_all_confirmations()

# NEW:
lineup_count, pitcher_count = self.get_cached_data(
    f'confirmations_{self.game_date}',
    self.confirmation_system.get_all_confirmations,
    'mlb_lineups'
)
```

In `enrich_with_statcast_priority` method:
```python
# OLD:
success = self.statcast_fetcher.enrich_player(player)

# NEW:
def fetch_statcast():
    return self.statcast_fetcher.enrich_player(player)

success = self.get_cached_data(
    f'statcast_{player.name}_{self.game_date}',
    fetch_statcast,
    'statcast'
)
```

## 2. GUI INTEGRATION (enhanced_dfs_gui.py)

### Add multi-lineup controls in create_control_panel:

```python
# After strategy selection, add:

# Multi-lineup section
multi_frame = QFrame()
multi_frame.setFrameStyle(QFrame.Box)
multi_layout = QVBoxLayout()

multi_label = QLabel("Multi-Lineup Settings:")
multi_label.setFont(QFont("Arial", 10, QFont.Bold))
multi_layout.addWidget(multi_label)

# Number of lineups
lineup_count_layout = QHBoxLayout()
lineup_count_layout.addWidget(QLabel("Number of Lineups:"))
self.lineup_count_spin = QSpinBox()
self.lineup_count_spin.setRange(1, 150)
self.lineup_count_spin.setValue(1)
self.lineup_count_spin.setToolTip("1 = Single lineup, 20 = Small GPP, 150 = Large GPP")
lineup_count_layout.addWidget(self.lineup_count_spin)
multi_layout.addLayout(lineup_count_layout)

multi_frame.setLayout(multi_layout)
control_layout.addWidget(multi_frame)
```

### Update optimize_lineup method:

```python
def optimize_lineup(self):
    # ... existing validation ...

    # Check if multi-lineup
    num_lineups = self.lineup_count_spin.value()

    if num_lineups > 1:
        # Multi-lineup generation
        lineups = self.core.generate_multiple_lineups(num_lineups)

        if lineups:
            # Show best lineup
            best_lineup, best_score, _ = lineups[0]
            self.display_lineup(best_lineup, best_score)

            self.console.append(f"\n✅ Generated {len(lineups)} lineups")
            self.console.append(f"📁 Saved upload file")
    else:
        # Single lineup (existing code)
        lineup, score = self.core.optimize_lineup_with_mode()
        if lineup:
            self.display_lineup(lineup, score)

            # Track performance
            self.core.track_lineup_performance(lineup, {
                'date': self.core.game_date,
                'type': 'single',
                'strategy': self.core.optimization_mode
            })
```

## 3. TESTING

Create test_upgrades.py:
```python
from bulletproof_dfs_core import BulletproofDFSCore

# Test caching
core = BulletproofDFSCore()
print("Testing smart cache...")

# Test multi-lineup
print("\nTesting multi-lineup generation...")
lineups = core.generate_multiple_lineups(5)

# Test tracking
print("\nTesting performance tracking...")
from performance_tracker import tracker
tracker.print_summary()
```

## 4. USAGE TIPS

1. Clear cache when needed:
   ```python
   from smart_cache import smart_cache
   smart_cache.clear('statcast')  # Clear specific
   smart_cache.clear()  # Clear all
   ```

2. Check performance:
   ```python
   from performance_tracker import tracker
   tracker.print_summary(30)  # Last 30 days
   ```

3. Generate lineups:
   - 1 lineup: Cash games
   - 3-5 lineups: Small GPPs
   - 20 lineups: Medium GPPs
   - 150 lineups: Large GPPs
