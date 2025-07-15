#!/usr/bin/env python3
"""
Quick Fix Script for DFS GUI Issues
===================================
Common fixes for when "nothing happens" after clicking buttons
"""

import os
import sys


def apply_fixes():
    """Apply common fixes for GUI issues"""
    print("🔧 DFS OPTIMIZER QUICK FIX")
    print("=" * 60)

    fixes_applied = []

    # Fix 1: Check if we're in the right directory
    print("\n1️⃣ Checking directory...")
    required_files = [
        'bulletproof_dfs_core.py',
        'unified_milp_optimizer.py',
        'unified_player_model.py'
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"❌ Missing files: {missing}")
        print("   Make sure you're running from the project directory!")
        return False
    else:
        print("✅ All core files present")

    # Fix 2: Create a wrapper for the GUI
    print("\n2️⃣ Creating GUI wrapper...")

    wrapper_code = '''#!/usr/bin/env python3
"""
Fixed GUI Launcher
==================
Wrapper that ensures proper error handling
"""

import streamlit as st
import sys
import traceback

# Add error handling
try:
    # Import the GUI
    from enhanced_dfs_gui import main as run_gui

    # Run with error catching
    try:
        run_gui()
    except Exception as e:
        st.error(f"❌ GUI Error: {str(e)}")
        st.code(traceback.format_exc())

        # Show recovery options
        st.info("🔧 Try these fixes:")
        st.code("""
# 1. Reinstall dependencies
pip install -r requirements.txt

# 2. Run diagnostic
python dfs_diagnostic.py

# 3. Test directly
python direct_test.py
        """)

except ImportError as e:
    st.error(f"❌ Import Error: {str(e)}")
    st.info("Run: pip install streamlit pandas numpy pulp")
'''

    with open('gui_fixed.py', 'w') as f:
        f.write(wrapper_code)

    print("✅ Created gui_fixed.py")
    fixes_applied.append("gui_fixed.py")

    # Fix 3: Create a simple working example
    print("\n3️⃣ Creating minimal working example...")

    minimal_code = '''#!/usr/bin/env python3
"""
Minimal Working DFS Optimizer
============================
Simplest possible working version
"""

import pandas as pd
from unified_milp_optimizer import UnifiedMILPOptimizer, OptimizationConfig
from unified_player_model import UnifiedPlayer

def optimize_csv(csv_file="DKSalaries5.csv"):
    """Simple optimization function"""
    # Load CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} players")

    # Create players
    players = []
    for _, row in df.iterrows():
        player = UnifiedPlayer(
            id=str(row['ID']),
            name=row['Name'],
            team=row['TeamAbbrev'],
            salary=int(row['Salary']),
            primary_position=row['Position'],
            positions=[row['Position']],
            base_projection=float(row['AvgPointsPerGame'])
        )
        # Set enhanced score
        player.enhanced_score = player.base_projection
        players.append(player)

    # Optimize
    optimizer = UnifiedMILPOptimizer(OptimizationConfig())
    lineup, score = optimizer.optimize_lineup(players, strategy="all_players")

    if lineup:
        print(f"\\n✅ Generated lineup! Score: {score:.2f}")
        print("\\nLINEUP:")
        for p in lineup:
            print(f"  {p.primary_position} {p.name} - ${p.salary:,}")
    else:
        print("❌ No lineup found")

    return lineup, score

if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "DKSalaries5.csv"
    optimize_csv(csv)
'''

    with open('minimal_optimizer.py', 'w') as f:
        f.write(minimal_code)

    print("✅ Created minimal_optimizer.py")
    fixes_applied.append("minimal_optimizer.py")

    # Fix 4: Create a batch file for Windows users
    if sys.platform == "win32":
        print("\n4️⃣ Creating Windows batch file...")

        batch_content = '''@echo off
echo Starting DFS Optimizer...
python -u enhanced_dfs_gui.py
pause
'''

        with open('run_optimizer.bat', 'w') as f:
            f.write(batch_content)

        print("✅ Created run_optimizer.bat")
        fixes_applied.append("run_optimizer.bat")

    # Fix 5: Create requirements check
    print("\n5️⃣ Creating requirements checker...")

    req_check = '''#!/usr/bin/env python3
"""Check and install requirements"""

import subprocess
import sys

required = [
    'streamlit',
    'pandas',
    'numpy',
    'pulp',
    'scikit-learn'
]

print("Checking requirements...")

for package in required:
    try:
        __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("\\n✅ All requirements satisfied!")
print("\\nNow run: streamlit run enhanced_dfs_gui.py")
'''

    with open('check_requirements.py', 'w') as f:
        f.write(req_check)

    print("✅ Created check_requirements.py")
    fixes_applied.append("check_requirements.py")

    # Summary
    print("\n" + "=" * 60)
    print("✅ FIXES APPLIED!")
    print("\n📋 Created files:")
    for f in fixes_applied:
        print(f"   - {f}")

    print("\n🚀 Next steps:")
    print("1. Test minimal version:  python minimal_optimizer.py")
    print("2. Run diagnostic:        python dfs_diagnostic.py")
    print("3. Try fixed GUI:         streamlit run gui_fixed.py")
    print("4. Check requirements:    python check_requirements.py")

    return True


if __name__ == "__main__":
    apply_fixes()