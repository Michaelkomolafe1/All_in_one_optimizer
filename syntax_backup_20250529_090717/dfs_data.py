
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


\n# AUTO-INJECTED: name matching\n
class StatcastIntegration:
    """Enhanced Statcast integration for DFS optimizer with recent performance awareness"""

    def __init__(self, cache_dir="data/statcast"):
        """Initialize the Statcast integration module"""
        self.cache_dir = cache_dir
        self.player_ids = {}
        self.force_refresh = False
        self.cache_expiry = 24  # Hours

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        self._load_player_ids()

        print(f"Statcast integration initialized with {len(self.player_ids)} player IDs")

    def set_force_refresh(self, force_refresh):
        """Set force refresh flag to override cache"""
        self.force_refresh = force_refresh
        print(f"Statcast force refresh set to: {force_refresh}")

    def _load_player_ids(self):
        """Load cached player IDs from a JSON file"""
        try:
            file_path = os.path.join(self.cache_dir, "player_ids.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.player_ids = json.load(f)
                print(f"Loaded {len(self.player_ids)} player IDs from cache")
        except Exception as e:
            print(f"Error loading player IDs: {e}")
            self.player_ids = {}

    def _generate_placeholder_metrics(self, player_name, is_pitcher):
        """Generate placeholder metrics for demo purposes"""
        import random

        if is_pitcher:
            return {
                "name": player_name,
                "xwOBA": round(random.uniform(0.250, 0.350), 3),
                "Hard_Hit": round(random.uniform(25, 45), 1),
                "Barrel": round(random.uniform(3, 12), 1),
                "K": round(random.uniform(15, 35), 1),
                "BB": round(random.uniform(5, 12), 1),
                "GB": round(random.uniform(35, 55), 1),
                "Whiff": round(random.uniform(15, 35), 1),
                "avg_velocity": round(random.uniform(90, 98), 1),
                "data_source": "placeholder (Statcast unavailable)"
            }
        else:
            return {
                "name": player_name,
                "xwOBA": round(random.uniform(0.280, 0.400), 3),
                "Hard_Hit": round(random.uniform(25, 50), 1),
                "Barrel": round(random.uniform(3, 15), 1),
                "K": round(random.uniform(10, 30), 1),
                "BB": round(random.uniform(5, 15), 1),
                "GB": round(random.uniform(30, 55), 1),
                "Pull": round(random.uniform(25, 55), 1),
                "avg_exit_velocity": round(random.uniform(85, 95), 1),
                "data_source": "placeholder (Statcast unavailable)"
            }

    def fetch_metrics(self, player_name, is_pitcher=False):
        """Fetch metrics for a player, with placeholder data for demo"""
        # Generate cache key
        cache_key = f"{player_name}_{'p' if is_pitcher else 'h'}"
        cache_key = cache_key.replace(' ', '_').replace("'", "").lower()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        # Check cache unless force refresh
        if os.path.exists(cache_file) and not self.force_refresh:
            cache_time = os.path.getmtime(cache_file)
            hours_old = (datetime.now() - datetime.fromtimestamp(cache_time)).total_seconds() / 3600

            if hours_old < self.cache_expiry:
                try:
                    with open(cache_file, 'r') as f:
                        metrics = json.load(f)
                        metrics['data_source'] = f"cached ({hours_old:.1f} hours old)"
                        return metrics
                except Exception as e:
                    print(f"Error reading cache for {player_name}: {e}")

        # Generate fresh placeholder metrics
        metrics = self._generate_placeholder_metrics(player_name, is_pitcher)

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"Error saving cache for {player_name}: {e}")

        return metrics

    def enrich_player_data(self, players, force_refresh=False):
        """Enrich player data with Statcast metrics"""
        self.set_force_refresh(force_refresh)

        enhanced_players = []
        print(f"Enriching {len(players)} players with Statcast metrics...")

        start_time = datetime.now()

        for i, player in enumerate(players):
            if i % 100 == 0 and i > 0:
                print(f"Processed {i}/{len(players)} players...")

            player_name = player[1]
            position = player[2]
            is_pitcher = position == "P"

            # Create a copy to avoid modifying the original
            enhanced_player = list(player)

            # Get metrics for this player
            metrics = self.fetch_metrics(player_name, is_pitcher)

            # Make sure we have at least 15 elements
            while len(enhanced_player) < 15:
                enhanced_player.append(None)

            # Add the metrics dictionary at index 14
            enhanced_player.append(metrics)

            enhanced_players.append(enhanced_player)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Enriched {len(enhanced_players)} players in {elapsed:.2f} seconds")
        return enhanced_players

    def print_metrics_summary(self, players_data):
        """Print a summary of the Statcast metrics to verify data quality"""
        print("\n===== STATCAST METRICS QUALITY REPORT =====")

        # Count metrics by source
        metrics_count = 0
        source_counts = {}
        pitcher_count = 0
        hitter_count = 0

        # Collect metrics
        for player in players_data:
            player_name = player[1]
            player_pos = player[2]

            if len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                metrics_count += 1

                # Count by source
                source = metrics.get('data_source', 'unknown')
                if source not in source_counts:
                    source_counts[source] = 0
                source_counts[source] += 1

                # Count by type
                if player_pos == 'P':
                    pitcher_count += 1
                else:
                    hitter_count += 1

        # Print summary
        print(
            f"Total players with metrics: {metrics_count}/{len(players_data)} ({metrics_count / len(players_data) * 100:.1f}%)")
        print(f"Pitchers with metrics: {pitcher_count}")
        print(f"Hitters with metrics: {hitter_count}")

        print("\nMetrics by source:")
        for source, count in source_counts.items():
            print(f"  - {source}: {count} players")

        # Print sample metrics
        print("\nSample metrics:")
        samples_shown = 0

        # First show a pitcher
        for player in players_data:
            if player[2] == 'P' and len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                print(f"\nPitcher: {player[1]} ({player[3]})")
                print(f"  Data source: {metrics.get('data_source', 'unknown')}")
                print(f"  Key metrics:")
                print(f"    - xwOBA: {metrics.get('xwOBA', 'N/A')}")
                print(f"    - Hard Hit%: {metrics.get('Hard_Hit', 'N/A')}")
                print(f"    - Barrel%: {metrics.get('Barrel', 'N/A')}")
                print(f"    - Velocity: {metrics.get('avg_velocity', 'N/A')}")
                print(f"    - Whiff%: {metrics.get('Whiff', 'N/A')}")
                samples_shown += 1
                break

        # Then show a hitter
        for player in players_data:
            if player[2] != 'P' and len(player) > 14 and isinstance(player[14], dict):
                metrics = player[14]
                print(f"\nHitter: {player[1]} ({player[3]})")
                print(f"  Data source: {metrics.get('data_source', 'unknown')}")
                print(f"  Key metrics:")
                print(f"    - xwOBA: {metrics.get('xwOBA', 'N/A')}")
                print(f"    - Hard Hit%: {metrics.get('Hard_Hit', 'N/A')}")
                print(f"    - Barrel%: {metrics.get('Barrel', 'N/A')}")
                print(f"    - Exit Velo: {metrics.get('avg_exit_velocity', 'N/A')}")
                samples_shown += 1
                break

        if samples_shown == 0:
            print("  No players found with Statcast metrics!")

        print("==========================================")