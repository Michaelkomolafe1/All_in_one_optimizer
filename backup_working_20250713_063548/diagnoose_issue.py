#!/usr/bin/env python3
"""Diagnose the exact issue with the modules"""

modules_to_check = [
    'unified_player_model',
    'unified_milp_optimizer',
    'bulletproof_dfs_core',
    'unified_scoring_engine'
]

for module_name in modules_to_check:
    print(f"\n{'=' * 60}")
    print(f"Checking {module_name}...")
    print('=' * 60)

    try:
        # Try to compile the file to find syntax errors
        with open(f"{module_name}.py", 'r') as f:
            content = f.read()

        compile(content, f"{module_name}.py", 'exec')
        print(f"✓ No syntax errors in {module_name}.py")

        # Try to import it
        module = __import__(module_name)
        print(f"✓ Successfully imported {module_name}")

    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR in {module_name}.py")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        print(f"   At position: {' ' * (e.offset - 1)}^")

    except Exception as e:
        print(f"❌ IMPORT ERROR in {module_name}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {str(e)}")

        # Try to find where the error occurs
        import traceback

        traceback.print_exc()