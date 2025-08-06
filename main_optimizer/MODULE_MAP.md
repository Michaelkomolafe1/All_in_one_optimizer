# MODULE MAP - Main Optimizer
## Last Updated: 2025-08-06 08:15:24

## Core Modules

### Essential Files (DO NOT DELETE)
- `unified_core_system_updated.py` - Main system orchestrator
- `unified_player_model.py` - Player data model
- `unified_milp_optimizer.py` - MILP optimization engine
- `unified_scoring_engine.py` - Consolidated scoring system
- `GUI.py` - Main GUI interface

### Configuration
- `correlation_scoring_config.py` - Scoring configuration
- `gui_strategy_configuration.py` - GUI strategy management
- `smart_enrichment_manager.py` - Data enrichment manager

### Strategy Modules
- `cash_strategies.py` - Cash game strategies
- `gpp_strategies.py` - GPP tournament strategies
- `strategy_selector.py` - Auto-strategy selection

### Data Integration
- `vegas_lines.py` - Vegas data integration
- `real_data_enrichments.py` - Statcast/real data
- `smart_confirmation.py` - Lineup confirmation

## Deprecated/Removable
The following can be safely removed after consolidation:
- `enhanced_scoring_engine.py` - Replaced by unified_scoring_engine
- `enhanced_scoring_engine_v2.py` - Replaced by unified_scoring_engine
- `pure_data_scoring_engine.py` - Merged into unified_scoring_engine
- Any `.backup` or `.bak` files

## Directory Structure
```
main_optimizer/
├── Core System Files
├── Strategy Files
├── Data Integration
├── GUI Components
└── Configuration
```
