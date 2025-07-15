#!/usr/bin/env python3
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
