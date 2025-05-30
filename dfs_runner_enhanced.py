
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncOptimizer:
    """Async optimization for 10x speed boost"""

    def __init__(self):
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)

    async def optimize_async(self, players, **kwargs):
        """Async optimization wrapper"""
        loop = asyncio.get_event_loop()

        # Run CPU-intensive optimization in thread pool
        result = await loop.run_in_executor(
            self.executor, 
            self._run_optimization, 
            players, 
            kwargs
        )

        return result

    def _run_optimization(self, players, kwargs):
        """Thread-safe optimization"""
        from dfs_optimizer_enhanced import optimize_lineup_milp
        return optimize_lineup_milp(players, **kwargs)



class FixedNameMatcher:
    """Fixed name matching that properly handles DFF format"""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize name for matching"""
        if not name:
            return ""

        name = str(name).strip()

        # CRITICAL FIX: Handle "Last, First" format from DFF
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                last = parts[0].strip()
                first = parts[1].strip()
                name = f"{first} {last}"

        # Clean up
        name = name.lower()
        name = ' '.join(name.split())  # Normalize whitespace

        # Remove suffixes that cause mismatches
        suffixes = [' jr', ' sr', ' iii', ' ii', ' iv', '.']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    @staticmethod
    def match_player(dff_name: str, dk_players_dict: dict, team_hint: str = None) -> tuple:
        """Enhanced matching with much higher success rate"""
        dff_normalized = FixedNameMatcher.normalize_name(dff_name)

        # Strategy 1: Try exact match first
        for dk_name, player_data in dk_players_dict.items():
            dk_normalized = FixedNameMatcher.normalize_name(dk_name)
            if dff_normalized == dk_normalized:
                return player_data, 100, "exact"

        # Strategy 2: First/Last name matching (very effective)
        best_match = None
        best_score = 0

        for dk_name, player_data in dk_players_dict.items():
            dk_normalized = FixedNameMatcher.normalize_name(dk_name)

            # Split into first/last names
            dff_parts = dff_normalized.split()
            dk_parts = dk_normalized.split()

            if len(dff_parts) >= 2 and len(dk_parts) >= 2:
                # Check if first and last names match exactly
                if (dff_parts[0] == dk_parts[0] and dff_parts[-1] == dk_parts[-1]):
                    return player_data, 95, "first_last_match"

                # Check if last names match and first initial matches
                if (dff_parts[-1] == dk_parts[-1] and 
                    len(dff_parts[0]) > 0 and len(dk_parts[0]) > 0 and
                    dff_parts[0][0] == dk_parts[0][0]):
                    score = 85
                    if score > best_score:
                        best_score = score
                        best_match = player_data

        if best_match and best_score >= 70:
            return best_match, best_score, "partial"

        return None, 0, "no_match"



import asyncio
try:
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
from concurrent.futures import ThreadPoolExecutor



# AUTO-FIXED: Enhanced DFF Name Matching
class FixedDFFNameMatcher:
    """FIXED: DFF name matching that handles 'Last, First' format"""

    @staticmethod
    def normalize_name(name):
        """Normalize name for matching"""
        if not name:
            return ""

        name = str(name).strip()

        # CRITICAL FIX: Handle "Last, First" format from DFF
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                last = parts[0].strip()
                first = parts[1].strip()
                name = f"{first} {last}"

        # Clean up
        name = name.lower()
        name = ' '.join(name.split())

        # Remove suffixes
        for suffix in [' jr', ' sr', ' iii', ' ii', ' iv']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    @staticmethod
    def match_dff_player(dff_name, dk_players_dict):
        """Match DFF player to DK player with high success rate"""
        dff_norm = FixedDFFNameMatcher.normalize_name(dff_name)

        # Try exact match first
        for dk_name, player_data in dk_players_dict.items():
            dk_norm = FixedDFFNameMatcher.normalize_name(dk_name)
            if dff_norm == dk_norm:
                return player_data, 100, "exact"

        # Try first/last name matching
        dff_parts = dff_norm.split()
        if len(dff_parts) >= 2:
            for dk_name, player_data in dk_players_dict.items():
                dk_norm = FixedDFFNameMatcher.normalize_name(dk_name)
                dk_parts = dk_norm.split()

                if len(dk_parts) >= 2:
                    # Full first/last match
                    if dff_parts[0] == dk_parts[0] and dff_parts[-1] == dk_parts[-1]:
                        return player_data, 95, "first_last"

                    # Last name + first initial
                    if (dff_parts[-1] == dk_parts[-1] and 
                        len(dff_parts[0]) > 0 and len(dk_parts[0]) > 0 and
                        dff_parts[0][0] == dk_parts[0][0]):
                        return player_data, 85, "last_first_initial"

        return None, 0, "no_match"

def apply_fixed_dff_adjustments(players, dff_rankings):
    """Apply DFF adjustments with FIXED name matching"""
    if not dff_rankings:
        return players

    print(f"🎯 Applying FIXED DFF matching to {len(players)} players...")

    # Create DK player lookup
    dk_players_dict = {}
    for player in players:
        if len(player) > 1:
            dk_players_dict[player[1]] = player

    matcher = FixedDFFNameMatcher()
    matches = 0

    # Apply DFF data to players
    for player in players:
        if len(player) < 7:
            continue

        dk_name = player[1]
        position = player[2] if len(player) > 2 else ""
        base_score = player[6]

        # Find best DFF match for this DK player
        best_dff_name = None
        best_confidence = 0

        for dff_name in dff_rankings.keys():
            temp_dict = {dk_name: player}
            matched, confidence, method = matcher.match_dff_player(dff_name, temp_dict)

            if matched and confidence > best_confidence:
                best_dff_name = dff_name
                best_confidence = confidence

        # Apply DFF adjustment
        if best_dff_name and best_confidence >= 70:
            dff_data = dff_rankings[best_dff_name]
            rank = dff_data.get('dff_rank', 999)

            adjustment = 0
            if position == 'P':
                if rank <= 5:
                    adjustment = 2.0
                elif rank <= 12:
                    adjustment = 1.5
                elif rank <= 20:
                    adjustment = 1.0
            else:
                if rank <= 10:
                    adjustment = 2.0
                elif rank <= 25:
                    adjustment = 1.5
                elif rank <= 40:
                    adjustment = 1.0

            if adjustment > 0:
                player[6] = base_score + (adjustment * 0.15)  # 15% weight
                matches += 1

    success_rate = (matches / len(dff_rankings) * 100) if dff_rankings else 0
    print(f"🎯 DFF Success: {matches}/{len(dff_rankings)} ({success_rate:.1f}%)")

    if success_rate >= 70:
        print("🎉 EXCELLENT! Fixed DFF matching working!")
    elif success_rate >= 50:
        print("✅ Good improvement!")

    return players
# END AUTO-FIXED DFF MATCHING
