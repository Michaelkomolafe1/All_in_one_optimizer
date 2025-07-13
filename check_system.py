#!/usr/bin/env python3
"""Quick system check to verify all modules are working"""

print("🔍 DFS OPTIMIZER SYSTEM CHECK")
print("=" * 50)

# Check imports
modules_to_check = [
    ("unified_player_model", "UnifiedPlayer"),
    ("unified_milp_optimizer", "UnifiedMILPOptimizer"),
    ("bulletproof_dfs_core", "BulletproofDFSCore"),
    ("unified_scoring_engine", "get_scoring_engine"),
    ("data_validator", "get_validator"),
    ("performance_optimizer", "get_performance_optimizer"),
]

import_status = {}

for module_name, class_name in modules_to_check:
    try:
        module = __import__(module_name)
        if hasattr(module, class_name):
            import_status[module_name] = "✅ OK"
        else:
            import_status[module_name] = f"⚠️ Missing {class_name}"
    except SyntaxError as e:
        import_status[module_name] = f"❌ Syntax Error: Line {e.lineno}"
    except ImportError as e:
        import_status[module_name] = f"❌ Import Error: {str(e)}"
    except Exception as e:
        import_status[module_name] = f"❌ Error: {str(e)}"

# Display results
print("\nMODULE STATUS:")
for module, status in import_status.items():
    print(f"  {module:.<30} {status}")

# Check if core system can initialize
print("\nCORE SYSTEM TEST:")
try:
    from bulletproof_dfs_core import BulletproofDFSCore

    core = BulletproofDFSCore()
    print("  ✅ Core system initialized successfully")

    # Check subsystems
    if hasattr(core, "scoring_engine") and core.scoring_engine:
        print("  ✅ Scoring engine available")
    else:
        print("  ⚠️ Scoring engine not available")

    if hasattr(core, "validator") and core.validator:
        print("  ✅ Validator available")
    else:
        print("  ⚠️ Validator not available")

except Exception as e:
    print(f"  ❌ Core initialization failed: {e}")

print("\n✅ System check complete!")
