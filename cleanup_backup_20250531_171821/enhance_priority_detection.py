#!/usr/bin/env python3
"""
Enhanced Priority Detection - Fixes priority player detection for real Statcast data
"""

def fix_priority_detection_in_core():
    """Fix the priority detection in your DFS core"""

    import os

    try:
        # Read your current core file
        with open("optimized_dfs_core_with_statcast.py", "r") as f:
            content = f.read()

        # Enhanced priority detection logic
        enhanced_logic = '''
def enhanced_priority_detection(players):
    """Enhanced priority detection that actually works"""

    priority_players = []

    for player in players:
        is_priority = False

        # Method 1: Manual selection (highest priority)
        if getattr(player, 'is_manual_selected', False):
            is_priority = True
            print(f"🎯 Manual priority: {player.name}")

        # Method 2: High DFF projection (8.0+)
        elif getattr(player, 'dff_projection', 0) >= 8.0:
            is_priority = True
            print(f"📈 High DFF projection: {player.name} ({player.dff_projection:.1f})")

        # Method 3: Confirmed order = YES
        elif hasattr(player, 'confirmed_order') and str(player.confirmed_order).upper() == 'YES':
            is_priority = True
            print(f"✅ DFF confirmed: {player.name}")

        # Method 4: High salary players (likely stars)
        elif getattr(player, 'salary', 0) >= 8000:
            is_priority = True
            print(f"💰 High salary: {player.name} (${player.salary})")

        # Method 5: Known top players
        elif player.name in ['Francisco Lindor', 'Pete Alonso', 'Christian Yelich', 
                           'Rafael Devers', 'Robbie Ray', 'Kodai Senga', 'Jose Altuve',
                           'Kyle Tucker', 'Aaron Judge', 'Mookie Betts', 'Shohei Ohtani']:
            is_priority = True
            print(f"⭐ Known star: {player.name}")

        if is_priority:
            priority_players.append(player)

    print(f"\n🎯 Total priority players identified: {len(priority_players)}")
    return priority_players

# Replace the existing priority detection
class EnhancedSimpleStatcastService:
    """Enhanced version that finds priority players better"""

    def __init__(self):
        try:
            from simple_statcast_fetcher import SimpleStatcastFetcher
            self.fetcher = SimpleStatcastFetcher()
            self.available = True
        except ImportError:
            self.fetcher = None
            self.available = False

    def enrich_priority_players(self, players):
        """Enhanced priority player enrichment"""
        if not self.fetcher:
            return players

        # Use enhanced priority detection
        priority_players = enhanced_priority_detection(players)

        if len(priority_players) == 0:
            print("⚠️ No priority players found - using top 10 by salary")
            # Fallback: use top 10 players by salary
            sorted_players = sorted(players, key=lambda x: getattr(x, 'salary', 0), reverse=True)
            priority_players = sorted_players[:10]
            for p in priority_players:
                print(f"💰 Fallback priority: {p.name} (${getattr(p, 'salary', 0)})")

        print(f"\n🔬 Fetching real Statcast data for {len(priority_players)} priority players...")

        successful_fetches = 0

        for player in priority_players:
            try:
                player_name = getattr(player, 'name', '')
                position = getattr(player, 'primary_position', '')

                if player_name and position:
                    print(f"🌐 Attempting: {player_name} ({position})")
                    statcast_data = self.fetcher.fetch_player_data(player_name, position)

                    if statcast_data:
                        # Apply to player
                        if hasattr(player, 'apply_statcast_data'):
                            player.apply_statcast_data(statcast_data)
                        elif hasattr(player, 'statcast_data'):
                            player.statcast_data = statcast_data
                            if hasattr(player, '_calculate_enhanced_score'):
                                player._calculate_enhanced_score()

                        print(f"✅ SUCCESS: {player_name}")
                        successful_fetches += 1
                    else:
                        print(f"❌ FAILED: {player_name}")

            except Exception as e:
                print(f"⚠️ Error with {player_name}: {e}")
                continue

        print(f"\n📊 Real Statcast Results:")
        print(f"   ✅ Successful: {successful_fetches}/{len(priority_players)}")
        print(f"   📈 Success rate: {(successful_fetches/len(priority_players)*100):.1f}%")

        return players
'''

        # Add the enhanced logic to the file
        enhanced_content = content + enhanced_logic

        with open("optimized_dfs_core_enhanced_priority.py", "w") as f:
            f.write(enhanced_content)

        print("✅ Created optimized_dfs_core_enhanced_priority.py")
        return True

    except Exception as e:
        print(f"❌ Enhancement failed: {e}")
        return False

if __name__ == "__main__":
    fix_priority_detection_in_core()
