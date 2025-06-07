#!/usr/bin/env python3
"""
COMPLETE MODULE VERIFICATION & INTEGRATION TEST
===============================================
Tests all DFS modules and shows what's working
"""

import os
import sys
from datetime import datetime

print("🧪 DFS MODULE VERIFICATION TEST")
print("=" * 60)

# Test imports
modules_status = {}

# 1. Core modules
try:
    from bulletproof_dfs_core import BulletproofDFSCore

    modules_status['Core'] = '✅'
except Exception as e:
    modules_status['Core'] = f'❌ {str(e)}'

# 2. Enhanced Stats
try:
    from enhanced_stats_engine import apply_enhanced_statistical_analysis

    modules_status['Enhanced Stats'] = '✅'
except:
    modules_status['Enhanced Stats'] = '❌'

# 3. Batting Order & Correlation
try:
    from batting_order_correlation_system import BattingOrderEnricher, CorrelationOptimizer

    modules_status['Batting Order'] = '✅'
except:
    modules_status['Batting Order'] = '❌'

# 4. Recent Form
try:
    from recent_form_analyzer import RecentFormAnalyzer

    modules_status['Recent Form'] = '✅'
except:
    modules_status['Recent Form'] = '❌'

# 5. Vegas Lines
try:
    from vegas_lines import VegasLines

    modules_status['Vegas Lines'] = '✅'
except:
    modules_status['Vegas Lines'] = '❌'

# 6. Smart Confirmations
try:
    from smart_confirmation_system import SmartConfirmationSystem

    modules_status['Confirmations'] = '✅'
except:
    modules_status['Confirmations'] = '❌'

# 7. Statcast
try:
    from simple_statcast_fetcher import FastStatcastFetcher

    modules_status['Statcast'] = '✅'
except:
    modules_status['Statcast'] = '❌'

# 8. Multi-lineup
try:
    from multi_lineup_optimizer import MultiLineupOptimizer

    modules_status['Multi-Lineup'] = '✅'
except:
    modules_status['Multi-Lineup'] = '❌'

# 9. Performance Tracker
try:
    from performance_tracker import tracker

    modules_status['Performance'] = '✅'
except:
    modules_status['Performance'] = '❌'

# 10. Smart Cache
try:
    from smart_cache import smart_cache

    modules_status['Smart Cache'] = '✅'
except:
    modules_status['Smart Cache'] = '❌'

print("\n📦 MODULE IMPORT STATUS:")
for module, status in modules_status.items():
    print(f"   {module}: {status}")

# Now test actual integration
print("\n🔧 INTEGRATION TEST:")
print("-" * 40)

if modules_status['Core'] == '✅':
    try:
        core = BulletproofDFSCore()

        # Check what's actually integrated
        integrated = []
        missing = []

        # Check batting order
        if hasattr(core, 'batting_enricher'):
            integrated.append("✅ Batting Order Enricher")
        else:
            missing.append("❌ Batting Order Enricher")

        if hasattr(core, 'correlation_optimizer'):
            integrated.append("✅ Correlation Optimizer")
        else:
            missing.append("❌ Correlation Optimizer")

        # Check form analyzer
        if hasattr(core, 'form_analyzer'):
            integrated.append("✅ Form Analyzer")
        else:
            missing.append("❌ Form Analyzer")

        # Check enrichment methods
        if hasattr(core, 'enrich_with_batting_order'):
            integrated.append("✅ enrich_with_batting_order method")
        else:
            missing.append("❌ enrich_with_batting_order method")

        if hasattr(core, 'enrich_with_recent_form'):
            integrated.append("✅ enrich_with_recent_form method")
        else:
            missing.append("❌ enrich_with_recent_form method")

        if hasattr(core, 'apply_lineup_correlations'):
            integrated.append("✅ apply_lineup_correlations method")
        else:
            missing.append("❌ apply_lineup_correlations method")

        print("\n✅ INTEGRATED:")
        for item in integrated:
            print(f"   {item}")

        if missing:
            print("\n❌ MISSING:")
            for item in missing:
                print(f"   {item}")

        # Test a quick pipeline
        print("\n🚀 TESTING PIPELINE:")

        # Load test CSV
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'DKSalaries' in f]
        if csv_files:
            test_csv = csv_files[0]
            print(f"   Using: {test_csv}")

            if core.load_draftkings_csv(test_csv):
                print("   ✅ CSV loaded")

                # Check if enrichment methods are called
                if hasattr(core, 'detect_confirmed_players'):
                    # Mock some confirmations
                    for player in core.players[:5]:
                        player.is_confirmed = True
                        player.is_manual_selected = True

                    # Test enrichments
                    print("\n   Testing enrichments:")

                    if hasattr(core, 'enrich_with_batting_order'):
                        count = core.enrich_with_batting_order()
                        print(f"   - Batting order: {count} players enriched")

                    if hasattr(core, 'enrich_with_recent_form'):
                        count = core.enrich_with_recent_form()
                        print(f"   - Recent form: {count} players enriched")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()

# Provide fixes if needed
print("\n" + "=" * 60)
print("📋 RECOMMENDATIONS:")

if '❌' in modules_status.values():
    print("\n1. Some modules failed to import. Check if files exist.")

if modules_status['Core'] == '✅':
    if 'missing' in locals() and missing:
        print("\n2. To fix missing integrations, add to BulletproofDFSCore.__init__:")
        print("""
# In __init__ method, after other initializations:

# Batting Order & Correlation
if BATTING_CORRELATION_AVAILABLE:
    integrate_batting_order_correlation(self)

# Recent Form Analyzer
if RECENT_FORM_AVAILABLE:
    from utils.cache_manager import cache
    self.form_analyzer = RecentFormAnalyzer(cache_manager=cache)
else:
    self.form_analyzer = None
""")

print("\n✅ Test complete!")