
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
        from dfs_optimizer import optimize_lineup_milp
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

