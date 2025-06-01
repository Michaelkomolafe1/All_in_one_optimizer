#!/usr/bin/env python3
"""
PuLP Wrapper - Avoids circular import issues
"""

# Import PuLP core without tests
try:
    import pulp.pulp as pulp_core
    from pulp.constants import *

    # Re-export the main classes we need
    LpProblem = pulp_core.LpProblem
    LpMaximize = pulp_core.LpMaximize
    LpMinimize = pulp_core.LpMinimize
    LpVariable = pulp_core.LpVariable
    LpBinary = pulp_core.LpBinary
    lpSum = pulp_core.lpSum
    LpStatus = pulp_core.LpStatus
    LpStatusOptimal = pulp_core.LpStatusOptimal
    PULP_CBC_CMD = pulp_core.PULP_CBC_CMD

    PULP_AVAILABLE = True
    print("✅ PuLP fixed - MILP optimization available")

except ImportError:
    # Fallback if PuLP is completely unavailable
    PULP_AVAILABLE = False
    print("⚠️ PuLP not available - using greedy optimization")
