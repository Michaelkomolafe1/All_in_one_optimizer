import random
import time
import sys
import os


def clean_player_data(players):
    """
    Clean and standardize player data to exactly 8 elements
    """
    cleaned_players = []

    for i, player in enumerate(players):
        try:
            # Ensure we have at least 8 elements
            if len(player) < 8:
                print(f"Warning: Player {i} has only {len(player)} elements: {player[:2]}")
                continue

            # Extract the core 8 elements we need
            player_id = player[0] if player[0] is not None else i + 1
            name = player[1] if player[1] else "Unknown"
            position = player[2] if player[2] else "UTIL"
            team = player[3] if player[3] else "UNK"
            salary = player[4] if player[4] is not None else 0
            proj_pts = player[5] if player[5] is not None else 0.0
            score = player[6] if player[6] is not None else 0.0
            batting_order = player[7] if len(player) > 7 else None

            # Validate critical fields
            if salary == 0 or score == 0:
                print(f"Warning: Player {name} has invalid salary ({salary}) or score ({score})")

            # Create clean player array with exactly 8 elements
            clean_player = [
                player_id,
                name,
                position,
                team,
                salary,
                proj_pts,
                score,
                batting_order
            ]

            cleaned_players.append(clean_player)

        except Exception as e:
            print(f"Error cleaning player {i}: {e}")
            continue

    return cleaned_players


def optimize_lineup(players, budget=50000, positions_needed={
    "P": 2, "C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1, "OF": 3
}, num_attempts=2000, min_team_stack=2, max_team_stack=5, stack_bonus=1.5, min_salary=0, contest_type="CASH"):
    """
    Optimize a DFS lineup based on player data and constraints, optimized for cash games
    """
    print(f"Running optimizer for {contest_type} games with {num_attempts} attempts...")

    # FIRST: Clean the player data
    players = clean_player_data(players)
    print(f"Cleaned {len(players)} players")

    # NEW: Expand multi-position players BEFORE optimization
    print("Expanding multi-position players...")
    expanded_players = expand_multi_position_players(players)

    # Use expanded players for the rest of the optimization
    players = expanded_players

    # Cash game specific adjustments
    if contest_type == "CASH":
        max_team_stack = min(max_team_stack, 4)
        stack_bonus = min(stack_bonus, 1.3)

    # Validate we have enough players for each position
    position_counts = {}
    for player in players:
        pos = player[2]
        if pos not in position_counts:
            position_counts[pos] = 0
        position_counts[pos] += 1

    print(f"Position counts: {position_counts}")

    # Check if we have enough players
    for position, needed in positions_needed.items():
        available = position_counts.get(position, 0)
        if available < needed:
            print(f"ERROR: Not enough {position} players. Need {needed}, have {available}")
            return None, 0

    # Group players by position
    players_by_position = {}
    for position in positions_needed.keys():
        players_by_position[position] = [p for p in players if p[2] == position]

        # Sort by score (descending)
        if contest_type == "CASH":
            # For cash games, prioritize confirmed players
            players_by_position[position].sort(
                key=lambda x: (
                    0 if (x[7] is not None) else 1,  # Confirmed first
                    -x[6]  # Then by score
                )
            )
        else:
            players_by_position[position].sort(key=lambda x: x[6], reverse=True)

        # Debug: Show top 3 players for each position
        print(f"\nTop 3 {position} players:")
        for p in players_by_position[position][:3]:
            print(f"  {p[1]} ({p[3]}) - ${p[4]:,} - Score: {p[6]:.1f}")

    # Group players by team for stacking (non-pitchers only)
    players_by_team = {}
    for player in players:
        if player[2] != "P":  # Only stack non-pitchers
            team = player[3]
            if team not in players_by_team:
                players_by_team[team] = []
            players_by_team[team].append(player)

    # Calculate team stack values
    teams_stack_value = []
    for team, team_players in players_by_team.items():
        if len(team_players) >= min_team_stack:
            # Sort by batting order then score
            team_players.sort(
                key=lambda x: (
                    x[7] if x[7] is not None else 999,
                    -x[6]
                )
            )

            # Calculate stack value (top 4 players)
            stack_value = sum(p[6] for p in team_players[:4])

            # Bonus for confirmed lineups in cash games
            if contest_type == "CASH":
                confirmed_count = sum(1 for p in team_players[:4] if p[7] is not None)
                stack_value *= (1 + (confirmed_count / 8))

            teams_stack_value.append((team, stack_value))

    # Sort teams by stack value
    teams_stack_value.sort(key=lambda x: x[1], reverse=True)
    top_stacking_teams = [t[0] for t in teams_stack_value[:5]]

    if top_stacking_teams:
        print(f"\nTop stacking teams: {', '.join(top_stacking_teams)}")
    else:
        print("\nNo teams available for stacking!")

    # Optimization variables
    best_lineup = None
    best_score = 0
    attempts_since_improvement = 0
    valid_lineups_found = 0

    stack_probability = 0.8 if contest_type == "CASH" else 0.7

    # Main optimization loop
    for attempt in range(num_attempts):
        if attempt % 100 == 0 and attempt > 0:
            print(f"Attempt {attempt}/{num_attempts} - Best: {best_score:.2f}, Valid: {valid_lineups_found}")

        lineup = []
        remaining_budget = budget
        positions_filled = {pos: 0 for pos in positions_needed}
        teams_used = {}

        # Decide if we're using a stack
        use_stack = random.random() < stack_probability and top_stacking_teams

        if use_stack:
            # Pick a stacking team
            stack_team = random.choice(top_stacking_teams)

            if stack_team in players_by_team:
                # Determine stack size
                stack_size = min(
                    random.randint(min_team_stack, max_team_stack),
                    len(players_by_team[stack_team]),
                    sum(positions_needed.values()) - positions_needed["P"]
                )

                # Add players from the stack
                stack_players = players_by_team[stack_team].copy()
                stack_players.sort(
                    key=lambda x: (
                        x[7] if x[7] is not None else 999,
                        -x[6]
                    )
                )

                for player in stack_players[:stack_size]:
                    position = player[2]
                    if positions_filled[position] < positions_needed[position] and player[4] <= remaining_budget:
                        lineup.append(player)
                        remaining_budget -= player[4]
                        positions_filled[position] += 1

                        team = player[3]
                        if team not in teams_used:
                            teams_used[team] = 0
                        teams_used[team] += 1

        # Fill remaining positions
        position_order = ["P", "C", "1B", "2B", "3B", "SS", "OF"]

        for position in position_order:
            slots_to_fill = positions_needed[position] - positions_filled[position]
            if slots_to_fill <= 0:
                continue

            # Get available players
            available_players = [
                p for p in players_by_position[position]
                if p not in lineup and p[4] <= remaining_budget
            ]

            # Add some randomness to avoid always picking the same players
            if len(available_players) > slots_to_fill + 2:
                # Keep top players but shuffle the rest
                top_count = min(3, len(available_players))
                top_players = available_players[:top_count]
                other_players = available_players[top_count:]
                random.shuffle(other_players)
                available_players = top_players + other_players

            # Fill slots
            filled = 0
            for player in available_players:
                if filled >= slots_to_fill:
                    break

                # Check team limit
                team = player[3]
                if position != "P" and team in teams_used and teams_used[team] >= max_team_stack:
                    continue

                # Check if we can afford this player
                if player[4] > remaining_budget:
                    continue

                lineup.append(player)
                remaining_budget -= player[4]
                filled += 1

                if team not in teams_used:
                    teams_used[team] = 0
                teams_used[team] += 1

        # Validate lineup
        if len(lineup) != sum(positions_needed.values()):
            continue

        # Check all positions are filled
        lineup_positions = {}
        for player in lineup:
            pos = player[2]
            if pos not in lineup_positions:
                lineup_positions[pos] = 0
            lineup_positions[pos] += 1

        is_valid = True
        for position, needed in positions_needed.items():
            if lineup_positions.get(position, 0) != needed:
                is_valid = False
                break

        if not is_valid:
            continue

        # Check salary constraints
        total_salary = sum(p[4] for p in lineup)
        if total_salary > budget or (min_salary > 0 and total_salary < min_salary):
            continue

        valid_lineups_found += 1

        # Calculate lineup score
        lineup_score = 0
        for player in lineup:
            player_score = player[6]

            # Apply stack bonus
            team = player[3]
            if player[2] != "P" and team in teams_used and teams_used[team] >= min_team_stack:
                bonus_multiplier = 1.0 + (stack_bonus - 1.0) * (teams_used[team] / 4.0)
                player_score *= bonus_multiplier

            # Cash game bonus for confirmed players
            if contest_type == "CASH" and player[2] != "P" and player[7] is not None:
                player_score *= 1.02

            lineup_score += player_score

        # Check if this is the best lineup
        if lineup_score > best_score:
            best_lineup = lineup
            best_score = lineup_score
            attempts_since_improvement = 0

            # Print the new best lineup
            print(f"\nNew best lineup found! Score: {best_score:.2f}")
            print(f"Total salary: ${total_salary:,}")
        else:
            attempts_since_improvement += 1

        # Early stopping
        if attempts_since_improvement >= num_attempts // 4:
            print(f"No improvement for {attempts_since_improvement} attempts. Stopping.")
            break

    print(f"\nOptimization complete. Found {valid_lineups_found} valid lineups.")

    if best_lineup:
        # NEW: Deduplicate any multi-position players in final lineup
        best_lineup = deduplicate_final_lineup(best_lineup)

        print(f"Final lineup validation after multi-position handling:")
        lineup_positions = {}
        for player in best_lineup:
            pos = player[2]
            if pos not in lineup_positions:
                lineup_positions[pos] = 0
            lineup_positions[pos] += 1
        print(f"Final position counts: {lineup_positions}")

    return best_lineup, best_score


def optimize_lineup_milp(players, budget=50000, num_attempts=1, min_team_stack=2, max_team_stack=4,
                         stack_bonus=0.0, min_salary=0, contest_type="CASH"):
    """
    Optimize a DFS lineup using Mixed Integer Linear Programming (MILP) - WITH MULTI-POSITION FIX
    """
    try:
    import pulp
    MILP_AVAILABLE = True
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - install with: pip install pulp")

    print(f"MILP Debug: Optimizing with {len(players)} players")

    # MULTI-POSITION FIX: Expand multi-position players BEFORE MILP optimization
    print("MILP: Expanding multi-position players...")
    expanded_players = expand_multi_position_players(players)
    players = expanded_players
    print(f"MILP: Using {len(players)} position-specific entries")

    # Print position counts after expansion
    pos_counts = {}
    for p in players:
        pos = p[2]
        if pos not in pos_counts:
            pos_counts[pos] = 0
        pos_counts[pos] += 1
    print(f"MILP Debug: Position counts after expansion: {pos_counts}")

    # Create a binary variable for each player
    player_vars = {}
    for i, player in enumerate(players):
        player_vars[i] = pulp.LpVariable(f"player_{i}", cat=pulp.LpBinary)

    # Create the optimization problem (maximize points)
    prob = pulp.LpProblem("DFS_Lineup_Optimization", pulp.LpMaximize)

    # Objective function: Maximize total projected points
    prob += pulp.lpSum([player_vars[i] * players[i][6] for i in range(len(players))])

    # Salary constraint
    prob += pulp.lpSum([player_vars[i] * players[i][4] for i in range(len(players))]) <= budget

    # Minimum salary constraint (if specified)
    if min_salary > 0:
        prob += pulp.lpSum([player_vars[i] * players[i][4] for i in range(len(players))]) >= min_salary

    # Total players constraint - must select exactly 10 players for MLB DFS
    prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 10

    # Position constraints for MLB
    position_constraints = {
        "P": 2,
        "C": 1,
        "1B": 1,
        "2B": 1,
        "3B": 1,
        "SS": 1,
        "OF": 3
    }

    for position, count in position_constraints.items():
        prob += pulp.lpSum([player_vars[i] for i in range(len(players))
                            if players[i][2] == position]) == count

        # Debug: Check if we have enough players for this position after expansion
        available = sum(1 for p in players if p[2] == position)
        if available < count:
            print(f"MILP Warning: Not enough {position} players! Need {count}, have {available}")

    # CRITICAL: Add constraint to prevent selecting the same player multiple times
    # (since multi-position players now have multiple entries)

    # Group players by name to prevent duplicates
    player_names = {}
    for i, player in enumerate(players):
        name = player[1]  # Player name is at index 1
        if name not in player_names:
            player_names[name] = []
        player_names[name].append(i)

    # Add constraint: each player can only be selected once across all positions
    for name, indices in player_names.items():
        if len(indices) > 1:  # Only add constraint for multi-position players
            prob += pulp.lpSum([player_vars[i] for i in indices]) <= 1
            print(f"MILP: Added uniqueness constraint for {name} (positions: {[players[i][2] for i in indices]})")

    # Check if stacking is possible before adding constraints
    teams = set([player[3] for player in players])
    possible_stacks = False
    for team in teams:
        # Count non-pitchers on this team
        team_batters = sum(1 for p in players if p[3] == team and p[2] != "P")
        if team_batters >= min_team_stack:
            possible_stacks = True
            break

    # Team stacking constraints
    if min_team_stack > 1 and possible_stacks:
        print(f"MILP Debug: Adding stacking constraints (min_stack={min_team_stack})")

        # Create binary variables for each team to indicate if it's stacked
        team_vars = {}
        for team in teams:
            team_vars[team] = pulp.LpVariable(f"team_{team}", cat=pulp.LpBinary)

        # Create variables to count how many players from each team
        team_count_vars = {}
        for team in teams:
            team_count_vars[team] = pulp.LpVariable(f"team_count_{team}",
                                                    lowBound=0,
                                                    upBound=9,  # Maximum 9 players per team
                                                    cat=pulp.LpInteger)

            # Set the team count variable
            prob += team_count_vars[team] == pulp.lpSum([player_vars[i] for i in range(len(players))
                                                         if players[i][3] == team])

            # If team is stacked, it must have at least min_team_stack players
            prob += team_count_vars[team] >= min_team_stack * team_vars[team]

            # If team count >= min_team_stack, then team_vars[team] must be 1
            prob += team_count_vars[team] <= 9 * team_vars[team]

            # Enforce maximum stack size
            prob += team_count_vars[team] <= max_team_stack

        # We must have at least one stacked team
        prob += pulp.lpSum([team_vars[team] for team in teams]) >= 1
    else:
        print(f"MILP Debug: Skipping stacking constraints - no teams with {min_team_stack}+ batters")
        min_team_stack = 1

    # Solve the problem
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print(f"MILP Debug: Solver status: {pulp.LpStatus[status]}")

    # If no solution found, try with relaxed constraints
    if pulp.LpStatus[status] != 'Optimal':
        print("No optimal solution found with current constraints!")

        # Try again with relaxed constraints if this was the first attempt
        if min_team_stack > 1:
            print("MILP Debug: Trying again with stacking disabled...")
            return optimize_lineup_milp(players, budget, num_attempts, 1, max_team_stack,
                                        stack_bonus, min_salary, contest_type)

        return None, 0

    # Get the selected players
    selected_indices = [i for i in range(len(players)) if player_vars[i].value() > 0.5]
    best_lineup = [players[i] for i in selected_indices]

    # MULTI-POSITION FIX: Deduplicate and validate final lineup
    best_lineup = deduplicate_final_lineup(best_lineup)

    print(f"MILP: Final lineup after deduplication has {len(best_lineup)} players")
    final_positions = {}
    for player in best_lineup:
        pos = player[2]
        final_positions[pos] = final_positions.get(pos, 0) + 1
    print(f"MILP: Final position distribution: {final_positions}")

    # Calculate the score
    best_score = sum(player[6] for player in best_lineup)

    # Sort the lineup by position
    position_order = {"P": 1, "C": 2, "1B": 3, "2B": 4, "3B": 5, "SS": 6, "OF": 7}
    best_lineup.sort(key=lambda x: position_order.get(x[2], 99))

    # Print team stacking info
    team_counts = {}
    for player in best_lineup:
        team = player[3]
        if team not in team_counts:
            team_counts[team] = 0
        team_counts[team] += 1

    stacks = [(team, count) for team, count in team_counts.items() if count >= min_team_stack]
    if stacks:
        stack_info = ", ".join([f"{team}: {count}" for team, count in stacks])
        print(f"MILP Debug: Found stack(s): {stack_info}")

    return best_lineup, best_score


def display_showdown_lineup(lineup, captain_index, verbose=True, contest_type="CASH"):
    """
    Format MLB Showdown lineup for display

    Args:
        lineup: List of player data
        captain_index: Index of the captain in the lineup
        verbose: Whether to show detailed information
        contest_type: Type of contest (CASH or GPP)

    Returns:
        Formatted lineup string
    """
    if not lineup:
        return "No valid lineup found."

    # Identify the captain
    captain = None
    for player in lineup:
        if player[0] == captain_index:
            captain = player
            break

    # If we didn't find the captain by ID, check by index position
    if not captain and lineup:
        for player in lineup:
            if lineup.index(player) == captain_index:
                captain = player
                break

    # If we still don't have a captain, use the first player
    if not captain and lineup:
        captain = lineup[0]

    # Get verbosity level if available
    verbosity = 1  # Default to normal
    try:
        def get_verbosity(): return 1
        verbosity = get_verbosity()
    except ImportError:
        verbosity = 2 if verbose else 1

    # Calculate totals
    captain_salary = captain[4] * 1.5 if captain else 0
    util_salary = sum(player[4] for player in lineup if player != captain)
    total_salary = captain_salary + util_salary

    captain_score = captain[6] * 1.5 if captain else 0
    util_score = sum(player[6] for player in lineup if player != captain)
    total_score = captain_score + util_score

    # Count teams
    teams = {}
    for player in lineup:
        team = player[3]
        if team not in teams:
            teams[team] = 0
        teams[team] += 1

    # Build the output
    output = ""

    # Header
    output += f"Optimized MLB Showdown Lineup for {contest_type} Games\n"
    output += "=" * 40 + "\n"
    output += f"Total Salary: ${total_salary:,.2f} / $50,000\n"

    # Score and other details
    if verbosity >= 1:
        output += f"Total Score: {total_score:.2f}\n"

        # Team breakdown
        team_str = ", ".join([f"{team} ({count})" for team, count in teams.items()])
        output += f"Team Breakdown: {team_str}\n"

    output += "\n"

    # Create data for the table
    table_data = []

    # Captain first
    if captain:
        if verbosity >= 2:
            # Detailed info for captain
            row = [
                "CPT",
                captain[1],  # Name
                captain[2],  # Position
                captain[3],  # Team
                f"${captain[4] * 1.5:,.0f}",  # Salary with 1.5x multiplier
                f"{captain[6] * 1.5:.2f}",  # Score with 1.5x multiplier
            ]

            # Add more detailed metrics if available
            if len(captain) > 7:
                row.append(f"{captain[7] if captain[7] is not None else '-'}")

            if len(captain) > 14 and isinstance(captain[14], dict):
                statcast = captain[14]
                if captain[2] == "P" and "xwOBA" in statcast:  # Pitcher
                    row.append(f"xwOBA: {statcast.get('xwOBA', 0):.3f}")
                elif "xwOBA" in statcast:  # Batter
                    row.append(f"xwOBA: {statcast.get('xwOBA', 0):.3f}")
                else:
                    row.append("-")
            else:
                row.append("-")
        else:
            # Basic info for captain
            row = [
                "CPT",
                captain[1],  # Name
                captain[2],  # Position
                captain[3],  # Team
                f"${captain[4] * 1.5:,.0f}"  # Salary with 1.5x multiplier
            ]

            if verbosity >= 1:
                row.append(f"{captain[6] * 1.5:.2f}")  # Score with 1.5x multiplier

        table_data.append(row)

    # UTIL players
    for player in lineup:
        if player != captain:
            if verbosity >= 2:
                # Detailed info for UTIL players
                row = [
                    "UTIL",
                    player[1],  # Name
                    player[2],  # Position
                    player[3],  # Team
                    f"${player[4]:,.0f}",  # Salary
                    f"{player[6]:.2f}",  # Score
                ]

                # Add more detailed metrics if available
                if len(player) > 7:
                    row.append(f"{player[7] if player[7] is not None else '-'}")

                if len(player) > 14 and isinstance(player[14], dict):
                    statcast = player[14]
                    if player[2] == "P" and "xwOBA" in statcast:  # Pitcher
                        row.append(f"xwOBA: {statcast.get('xwOBA', 0):.3f}")
                    elif "xwOBA" in statcast:  # Batter
                        row.append(f"xwOBA: {statcast.get('xwOBA', 0):.3f}")
                    else:
                        row.append("-")
                else:
                    row.append("-")
            else:
                # Basic info for UTIL players
                row = [
                    "UTIL",
                    player[1],  # Name
                    player[2],  # Position
                    player[3],  # Team
                    f"${player[4]:,.0f}"  # Salary
                ]

                if verbosity >= 1:
                    row.append(f"{player[6]:.2f}")  # Score

            table_data.append(row)

    # Format as table
    if verbosity >= 1:
        # Headers based on verbosity
        if verbosity >= 2:
            headers = ["Slot", "Player", "Pos", "Team", "Salary", "Score", "Bat", "Stat"]
        else:
            headers = ["Slot", "Player", "Pos", "Team", "Salary", "Score"]

        output += tabulate_simple(table_data, headers=headers[:len(table_data[0])])
    else:
        # Simple list for quiet mode
        for row in table_data:
            output += f"{row[0]}: {row[1]} ({row[2]}, {row[3]}) - {row[4]}\n"

    # Add DraftKings import format
    output += "\n\nDraftKings Import Format:\n"

    # Start with captain
    dk_format = []
    if captain:
        dk_format.append(captain[1])

    # Then add UTIL players
    for player in lineup:
        if player != captain:
            dk_format.append(player[1])

    output += ", ".join(dk_format)

    # Add cash game tips
    if contest_type == "CASH" and verbosity >= 1:
        output += "\n\nCash Game Notes:\n"
        output += "• Captain selections have higher variance - choose reliable players\n"
        output += "• Pitchers as captain can provide consistent scoring\n"
        output += "• Verify lineups before contest lock\n"
        output += "• Balance exposure to both teams for safety\n"

    return output


def optimize_showdown_milp(players, budget=50000, captain_boost=1.5, min_salary=0,
                           contest_type="CASH"):
    """
    Optimize a MLB Showdown lineup using Mixed Integer Linear Programming (MILP) - WITH MULTI-POSITION FIX
    """
    try:
    import pulp
    MILP_AVAILABLE = True
except ImportError:
    MILP_AVAILABLE = False
    print("⚠️ PuLP not available - install with: pip install pulp")

    print(f"Showdown Debug: Optimizing lineup with {len(players)} players")

    # MULTI-POSITION FIX: Expand multi-position players BEFORE optimization
    print("Showdown: Expanding multi-position players...")
    expanded_players = expand_multi_position_players(players)
    players = expanded_players
    print(f"Showdown: Using {len(players)} position-specific entries")

    # Identify teams in the player pool
    teams = set(player[3] for player in players)
    print(f"Showdown Debug: Teams in player pool: {', '.join(teams)}")

    # Create the optimization problem (maximize points)
    prob = pulp.LpProblem("MLB_Showdown_Optimization", pulp.LpMaximize)

    # Create binary variables for selecting players (0 = not selected, 1 = selected)
    player_vars = {}
    for i, player in enumerate(players):
        player_vars[i] = pulp.LpVariable(f"player_{i}", cat=pulp.LpBinary)

    # Create binary variables for selecting captains (0 = not captain, 1 = captain)
    captain_vars = {}
    for i, player in enumerate(players):
        captain_vars[i] = pulp.LpVariable(f"captain_{i}", cat=pulp.LpBinary)

    # Objective function: Maximize total projected points
    # UTIL players get 1x points, captain gets captain_boost multiplier
    prob += pulp.lpSum([
        # Normal points for all selected players
        player_vars[i] * players[i][6] +
        # Extra points for captain (captain_boost-1 because we already counted 1x above)
        captain_vars[i] * players[i][6] * (captain_boost - 1)
        for i in range(len(players))
    ])

    # Constraint: Total of 6 players
    prob += pulp.lpSum([player_vars[i] for i in range(len(players))]) == 6

    # Constraint: Exactly one captain
    prob += pulp.lpSum([captain_vars[i] for i in range(len(players))]) == 1

    # Constraint: Captain must be selected as a player
    for i in range(len(players)):
        prob += captain_vars[i] <= player_vars[i]

    # Salary constraint - captains cost 1.5x
    prob += pulp.lpSum([
        # Normal salary for all selected players
        player_vars[i] * players[i][4] +
        # Extra salary for captain (0.5x because we already counted 1x above)
        captain_vars[i] * players[i][4] * 0.5
        for i in range(len(players))
    ]) <= budget

    # Minimum salary constraint (if specified)
    if min_salary > 0:
        prob += pulp.lpSum([
            player_vars[i] * players[i][4] +
            captain_vars[i] * players[i][4] * 0.5
            for i in range(len(players))
        ]) >= min_salary

    # MULTI-POSITION FIX: Add constraint to prevent selecting the same player multiple times
    # Group players by name to prevent duplicates
    player_names = {}
    for i, player in enumerate(players):
        name = player[1]  # Player name is at index 1
        if name not in player_names:
            player_names[name] = []
        player_names[name].append(i)

    # Add constraint: each player can only be selected once across all positions
    for name, indices in player_names.items():
        if len(indices) > 1:  # Only add constraint for multi-position players
            prob += pulp.lpSum([player_vars[i] for i in indices]) <= 1
            print(f"Showdown: Added uniqueness constraint for {name}")

    # Team balance - need to have players from BOTH teams (if we have 2+ teams)
    if len(teams) >= 2:
        # Find the two teams with the most players (likely the matchup teams)
        team_counts = {}
        for player in players:
            team = player[3]
            if team not in team_counts:
                team_counts[team] = 0
            team_counts[team] += 1

        # Sort teams by player count, descending
        teams_sorted = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)
        matchup_teams = [team for team, _ in teams_sorted[:2]]

        print(f"Showdown Debug: Matchup appears to be {matchup_teams[0]} vs {matchup_teams[1]}")

        # Create binary variables for each team used
        team_used_vars = {}
        for team in matchup_teams:
            team_used_vars[team] = pulp.LpVariable(f"team_used_{team}", cat=pulp.LpBinary)

            # If any player from this team is selected, team_used must be 1
            for i, player in enumerate(players):
                if player[3] == team:
                    prob += team_used_vars[team] >= player_vars[i]

            # If no players from this team are selected, team_used must be 0
            prob += team_used_vars[team] <= pulp.lpSum([
                player_vars[i] for i in range(len(players)) if players[i][3] == team
            ])

        # Must use both matchup teams
        for team in matchup_teams:
            prob += team_used_vars[team] == 1

        # For cash games, ensure more balanced distribution
        if contest_type == "CASH":
            for team in matchup_teams:
                # At least 2 players from each team
                prob += pulp.lpSum([
                    player_vars[i] for i in range(len(players)) if players[i][3] == team
                ]) >= 2

                # At most 4 players from one team (for balance)
                prob += pulp.lpSum([
                    player_vars[i] for i in range(len(players)) if players[i][3] == team
                ]) <= 4

    # Solve the problem
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print(f"Showdown Debug: Solver status: {pulp.LpStatus[status]}")

    # Check if a solution was found
    if pulp.LpStatus[status] != 'Optimal':
        print("No optimal Showdown lineup found!")

        # Try again with relaxed constraints if using cash game settings
        if contest_type == "CASH":
            print("Showdown Debug: Trying again without cash game balance constraints...")
            return optimize_showdown_milp(players, budget, captain_boost, min_salary, "GPP")

        return None, 0, None

    # Get the selected players
    selected_indices = [i for i in range(len(players)) if player_vars[i].value() > 0.5]
    captain_index = next((i for i in range(len(players)) if captain_vars[i].value() > 0.5), None)

    if captain_index is None:
        print("Error: No captain selected in solution!")
        return None, 0, None

    best_lineup = [players[i] for i in selected_indices]

    # MULTI-POSITION FIX: Deduplicate final lineup
    best_lineup = deduplicate_final_lineup(best_lineup)
    print(f"Showdown: Final lineup after deduplication has {len(best_lineup)} players")

    # Calculate the score
    best_score = 0
    for player in best_lineup:
        player_name = player[1]
        # Find if this player is the captain
        is_captain = False
        for i in selected_indices:
            if players[i][1] == player_name and captain_vars[i].value() > 0.5:
                is_captain = True
                captain_index = players[i][0]  # Update captain index to player ID
                break

        if is_captain:
            best_score += player[6] * captain_boost
        else:
            best_score += player[6]

    # Print lineup summary
    print(f"Showdown Debug: Found lineup with score {best_score:.2f}")
    if best_lineup:
        captain_name = next((p[1] for p in best_lineup if p[0] == captain_index), "Unknown")
        print(f"Showdown Debug: Captain is {captain_name}")

    # Count players per team
    team_counts = {}
    for player in best_lineup:
        team = player[3]
        if team not in team_counts:
            team_counts[team] = 0
        team_counts[team] += 1

    team_breakdown = ", ".join([f"{team}: {count}" for team, count in team_counts.items()])
    print(f"Showdown Debug: Team breakdown: {team_breakdown}")

    return best_lineup, best_score, captain_index





def tabulate_simple(data, headers=None):
    """Simple tabulate function if tabulate package isn't available"""
    if not data:
        return ""

    # Calculate column widths
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data

    col_widths = []
    for col_idx in range(len(all_rows[0])):
        col_widths.append(max(len(str(row[col_idx])) for row in all_rows) + 2)

    # Generate the table
    output = []

    # Headers
    if headers:
        header_row = ""
        for i, header in enumerate(headers):
            header_row += str(header).ljust(col_widths[i])
        output.append(header_row)
        output.append("-" * sum(col_widths))

    # Data rows
    for row in data:
        data_row = ""
        for i, cell in enumerate(row):
            data_row += str(cell).ljust(col_widths[i])
        output.append(data_row)

    return "\n".join(output)


def calculate_actual_score(lineup, min_team_stack, stack_bonus):
    """Calculate actual lineup score with stack bonuses"""
    # Count players per team (excluding pitchers)
    team_counts = {}
    for player in lineup:
        if player[2] != "P":  # Not a pitcher
            team = player[3]
            if team not in team_counts:
                team_counts[team] = 0
            team_counts[team] += 1

    # Calculate score with stack bonuses
    score = 0
    for player in lineup:
        player_score = player[6]  # Base score

        # Apply stack bonus for non-pitchers
        if player[2] != "P":
            team = player[3]
            if team in team_counts and team_counts[team] >= min_team_stack:
                # Scale bonus based on stack size
                bonus_multiplier = 1.0 + (stack_bonus - 1.0) * (team_counts[team] / 4.0)
                player_score *= bonus_multiplier

        score += player_score

    return score

"""
Part 3: Modify display_lineup function in dfs_optimizer.py for simpler output control
"""


def display_lineup(lineup, verbose=True, contest_type="CASH"):
    """
    Format lineup for display with adjustable verbosity

    Args:
        lineup: List of player data
        verbose: Whether to print detailed info
        contest_type: CASH or GPP for display customization

    Returns:
        Formatted lineup string
    """
    if not lineup:
        return "No valid lineup found."

    # Get verbosity level from imported module (if available)
    # Otherwise use the verbose parameter (backwards compatibility)
    verbosity = 1  # Default to normal
    try:
        def get_verbosity(): return 1
        verbosity = get_verbosity()

# Multi-position player optimization improvements
# This optimizer now properly handles players eligible for multiple positions
# Players like "1B/OF Eric Wagaman" will have separate entries for each position

    except ImportError:
        verbosity = 2 if verbose else 1

    # Sort by position in standard order
    position_order = {"P": 0, "C": 1, "1B": 2, "2B": 3, "3B": 4, "SS": 5, "OF": 6}
    sorted_lineup = sorted(lineup, key=lambda x: (position_order.get(x[2], 99),
                                                  x[2],
                                                  -x[6]))  # Sort by position, then score

    # Calculate totals
    total_salary = sum(player[4] for player in sorted_lineup)
    total_score = sum(player[6] for player in sorted_lineup)

    # Count teams (for stacks)
    team_counts = {}
    for player in sorted_lineup:
        team = player[3]
        if team not in team_counts:
            team_counts[team] = 0
        team_counts[team] += 1

    # ENHANCEMENT: Calculate cash game specific metrics
    confirmed_count = 0
    non_pitcher_count = 0
    confirmation_percentage = 0

    if contest_type == "CASH":
        # Check for confirmed players - a player is confirmed if they have a batting order (index 7)
        for p in sorted_lineup:
            if p[2] != "P":  # Not a pitcher
                non_pitcher_count += 1
                # Check if they have batting order
                if p[7] is not None and str(p[7]).strip() != "" and str(p[7]).strip() != "None":
                    confirmed_count += 1

        if non_pitcher_count > 0:
            confirmation_percentage = confirmed_count / non_pitcher_count * 100

    # Build the output
    output = ""

    # Header is always shown
    output += f"Optimized DFS Lineup for {contest_type} Games\n"
    if verbosity >= 1:
        output += "=" * 40 + "\n"
    output += f"Total Salary: ${total_salary:,} / $50,000\n"

    # Score and other details (normal+ verbosity)
    if verbosity >= 1:
        output += f"Total Score: {total_score:.1f}\n"

        # CASH game metrics
        if contest_type == "CASH":
            output += f"Confirmed Players: {confirmed_count}/{non_pitcher_count} ({confirmation_percentage:.1f}%)\n"

        # Team stacks
        stacks = [(team, count) for team, count in team_counts.items() if count >= 2]
        if stacks:
            stacks.sort(key=lambda x: x[1], reverse=True)
            stack_str = ", ".join([f"{team} ({count})" for team, count in stacks])
            output += f"Team Stacks: {stack_str}\n"

    output += "\n"

    # Create data for the table
    table_data = []
    for player in sorted_lineup:
        # Default row with basic info (position, name, team, salary)
        row = [
            player[2],  # Position
            player[1],  # Name
            player[3],  # Team
            f"${player[4]:,}",  # Salary
        ]

        # Add score for normal+ verbosity
        if verbosity >= 1:
            row.append(f"{player[6]:.1f}")  # Score

            # Add batting order if available
            batting_order = player[7] if len(player) > 7 else None
            has_batting_order = (batting_order is not None and
                                 str(batting_order).strip() != "" and
                                 str(batting_order).strip() != "None")

            if has_batting_order:
                row.append(f"{batting_order}")
            else:
                row.append("-")

        # Add advanced stats for verbose mode
        if verbosity >= 2:
            # Add projection if available
            if player[5] and player[5] > 0:
                row.append(f"{player[5]:.1f}")
            else:
                row.append("-")

            # Add Statcast metrics if available (simplified)
            if len(player) > 14 and isinstance(player[14], dict):
                statcast = player[14]
                key_stat = ""

                # Choose most relevant stat based on position
                if player[2] == "P":  # Pitcher
                    if "xwOBA" in statcast:
                        key_stat = f"xwOBA: {statcast.get('xwOBA', 0):.3f}"
                else:  # Batter
                    if "xwOBA" in statcast:
                        key_stat = f"xwOBA: {statcast.get('xwOBA', 0):.3f}"

                row.append(key_stat)
            else:
                row.append("")  # No Statcast data

        # Always update the name with indicators
        player_name = player[1]

        # Add team stack indicator as * if in a stack
        if team_counts.get(player[3], 0) >= 2 and player[2] != "P":
            player_name = f"{player_name} *"

        # Add confirmed lineup indicator as ✓
        if has_batting_order and player[2] != "P":
            player_name = f"{player_name} ✓"

        row[1] = player_name  # Update the name

        table_data.append(row)

    # Format as table
    if verbosity >= 1:
        # Headers based on verbosity
        if verbosity >= 2:
            headers = ["POS", "Player", "Team", "Salary", "Score", "Bat", "Proj", "Stat"]
        else:
            headers = ["POS", "Player", "Team", "Salary", "Score", "Bat"]

        output += tabulate_simple(table_data, headers=headers[:len(row)])
    else:
        # Simple list for quiet mode
        for row in table_data:
            output += f"{row[0]}: {row[1]}\n"

    # Always include DraftKings import format
    output += "\n\nDraftKings Import Format:\n"
    dk_positions = ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"]
    dk_lineup = []

    for pos in dk_positions:
        for player in sorted_lineup:
            if player[2] == pos and player not in dk_lineup:
                dk_lineup.append(player)
                break

    output += ", ".join(player[1] for player in dk_lineup)

    # Add cash game tips at normal+ verbosity
    if contest_type == "CASH" and verbosity >= 1:
        output += "\n\nCash Game Notes:\n"
        if confirmation_percentage < 75:
            output += "⚠️ Warning: Less than 75% of batters are confirmed in lineups. Check for late lineup news.\n"

        output += "Remember to verify all players are in today's starting lineups before contests lock."

    return output


def tabulate_simple(data, headers=None):
    """Simple tabulate function if tabulate package isn't available"""
    if not data:
        return ""

    # Calculate column widths
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data

    col_widths = []
    for col_idx in range(len(all_rows[0])):
        col_widths.append(max(len(str(row[col_idx])) for row in all_rows) + 2)

    # Generate the table
    output = []

    # Headers
    if headers:
        header_row = ""
        for i, header in enumerate(headers):
            header_row += str(header).ljust(col_widths[i])
        output.append(header_row)
        output.append("-" * sum(col_widths))

    # Data rows
    for row in data:
        data_row = ""
        for i, cell in enumerate(row):
            data_row += str(cell).ljust(col_widths[i])
        output.append(data_row)

    return "\n".join(output)


def debug_player_data(players, lineup):
    """Print detailed information about player data structure"""
    print("\n===== PLAYER DATA DIAGNOSTIC =====")

    # Show sample of original players
    if players:
        print("\nExample player from original data:")
        sample = players[0]
        for i, value in enumerate(sample):
            print(f"  Index {i}: {value} (type: {type(value).__name__})")

    # Show all lineup players
    print("\nPlayers in final lineup:")
    for i, player in enumerate(lineup):
        name = player[1]
        pos = player[2]
        batting_order = player[7] if len(player) > 7 else None
        print(f"{i + 1}. {name} ({pos}) - Batting order: {batting_order} (type: {type(batting_order).__name__})")

    # Check if there's a mismatch in the data structure
    print("\nChecking for position mismatch issues:")
    positions_in_lineup = {player[2] for player in lineup}
    print(f"Positions in lineup: {positions_in_lineup}")

    # Check batting order data
    print("\nBatting order values:")
    for player in lineup:
        if player[2] != "P":  # Only check non-pitchers
            name = player[1]
            bat_order = player[7] if len(player) > 7 else None
            print(f"{name}: {bat_order} (type: {type(bat_order).__name__})")

    # Count confirmed players explicitly
    confirmed_count = sum(
        1 for p in lineup if p[2] != "P" and p[7] is not None and p[7] != "None" and str(p[7]).strip() != "")
    non_pitcher_count = sum(1 for p in lineup if p[2] != "P")
    print(f"\nConfirmed players: {confirmed_count}/{non_pitcher_count}")

    print("===== END DIAGNOSTIC =====\n")


def expand_multi_position_players(players):
    """
    Expand multi-position players into multiple entries for each position they can play.
    This allows the optimizer to assign them to any of their eligible positions.

    Args:
        players: List of player data [id, name, position, team, salary, proj, score, batting_order, ...]

    Returns:
        Expanded list with separate entries for each position a player can play
    """
    expanded_players = []

    for player in players:
        position = player[2]  # Position is at index 2

        # Check if this is a multi-position player
        if '/' in position:
            eligible_positions = position.split('/')

            # Create a separate entry for each position
            for pos in eligible_positions:
                pos = pos.strip()  # Remove any whitespace

                # Create a copy of the player data
                expanded_player = list(player)
                expanded_player[2] = pos  # Set the single position

                # Add position flexibility indicator
                if len(expanded_player) < 18:
                    expanded_player.extend([None] * (18 - len(expanded_player)))
                expanded_player[17] = {
                    'original_position': position,
                    'eligible_positions': eligible_positions,
                    'is_multi_position': True
                }

                expanded_players.append(expanded_player)
        else:
            # Single position player - add as-is with indicator
            single_player = list(player)
            if len(single_player) < 18:
                single_player.extend([None] * (18 - len(single_player)))
            single_player[17] = {
                'original_position': position,
                'eligible_positions': [position],
                'is_multi_position': False
            }
            expanded_players.append(single_player)

    print(f"Expanded {len(players)} players to {len(expanded_players)} position-specific entries")
    return expanded_players


def deduplicate_final_lineup(lineup):
    """
    Remove duplicate players from final lineup (since multi-position players
    may have been selected for multiple positions during optimization).

    Keep the version that provides the best positional fit.
    """
    seen_players = {}
    final_lineup = []

    for player in lineup:
        player_name = player[1]  # Name is at index 1

        if player_name not in seen_players:
            seen_players[player_name] = player
            final_lineup.append(player)
        else:
            # Player already in lineup - this shouldn't happen with proper constraints
            print(f"Warning: Duplicate player {player_name} found in lineup")

    return final_lineup


def tabulate_simple(data, headers=None):
    """Simple tabulate function if tabulate package isn't available"""
    if not data:
        return ""

    # Calculate column widths
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data

    col_widths = []
    for col_idx in range(len(all_rows[0])):
        col_widths.append(max(len(str(row[col_idx])) for row in all_rows) + 2)

    # Generate the table
    output = []

    # Headers
    if headers:
        header_row = ""
        for i, header in enumerate(headers):
            header_row += str(header).ljust(col_widths[i])
        output.append(header_row)
        output.append("-" * sum(col_widths))

    # Data rows
    for row in data:
        data_row = ""
        for i, cell in enumerate(row):
            data_row += str(cell).ljust(col_widths[i])
        output.append(data_row)

    return "\n".join(output)