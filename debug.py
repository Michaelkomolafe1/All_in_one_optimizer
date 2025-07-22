#!/usr/bin/env python3
"""
COMPLETE METHOD REPLACEMENTS WITH CONTEXT
=========================================
Shows exactly where each method goes in unified_core_system.py
"""

print("\n📄 COMPLETE METHOD REPLACEMENTS FOR unified_core_system.py")
print("=" * 70)

# ===========================================================================
# METHOD 1: _call_optimizer (Add this new method to the class)
# ===========================================================================
print("\n1️⃣ ADD THIS NEW METHOD TO UnifiedCoreSystem CLASS:")
print("-" * 70)

method_1 = '''    def _call_optimizer(self, players, strategy, min_salary_val, existing_lineups=None):
        """
        Call the optimizer with correct parameters
        Note: UnifiedMILPOptimizer doesn't use min_salary parameter
        """
        try:
            # The optimize_lineup method only accepts: players, strategy, manual_selections
            lineup_players, score = self.optimizer.optimize_lineup(
                players=players,
                strategy=strategy,
                manual_selections=""  # Empty string for no manual selections
            )
            return lineup_players, score
        except Exception as e:
            print(f"   ❌ Optimization error: {e}")
            raise'''

print(method_1)

# ===========================================================================
# METHOD 2: Complete enrich_player_pool replacement
# ===========================================================================
print("\n\n2️⃣ REPLACE THE ENTIRE enrich_player_pool METHOD:")
print("-" * 70)

method_2 = '''    def enrich_player_pool(self) -> int:
        """
        Enrich player pool with all available data sources

        Returns:
            Number of players enriched
        """
        if not self.player_pool:
            return 0

        print(f"\\n🔄 Enriching {len(self.player_pool)} players with ALL data sources...")

        # 1. Fetch Vegas data for all teams
        print("\\n📊 Fetching Vegas lines...")
        vegas_data = {}
        try:
            # Get unique games
            games = set()
            for player in self.player_pool:
                if hasattr(player, 'game_info') and player.game_info:
                    games.add(player.game_info)

            # Fetch vegas data for each game
            for game in games:
                try:
                    # Parse teams from game info (format: "TEA@TEB 07:10PM ET")
                    teams = game.split()[0].split('@')
                    if len(teams) == 2:
                        away_team, home_team = teams
                        # Fetch lines
                        lines = self.vegas.fetch_lines(home_team, away_team)
                        if lines:
                            vegas_data[home_team] = lines
                            vegas_data[away_team] = lines
                except:
                    continue

            print(f"   ✅ Fetched Vegas data for {len(vegas_data)} teams")
        except Exception as e:
            logger.error(f"Vegas fetch error: {e}")

        # 2. Fetch Statcast data
        print("\\n⚾ Fetching Statcast data...")
        statcast_data = {}
        try:
            # Use the correct method name: fetch_statcast_batch
            if hasattr(self.statcast, 'fetch_statcast_batch'):
                # Batch fetch with correct method
                statcast_results = self.statcast.fetch_statcast_batch(
                    self.player_pool  # Pass player objects, not just names
                )

                for name, stats in statcast_results.items():
                    if stats is not None:
                        statcast_data[name] = stats
            else:
                # Individual fetch as backup
                for player in self.player_pool[:20]:  # Limit to avoid rate limits
                    try:
                        data = self.statcast.fetch_player_data(player.name)
                        if data is not None:
                            statcast_data[player.name] = data
                    except:
                        pass

            print(f"   ✅ Fetched Statcast data for {len(statcast_data)} players")
        except Exception as e:
            logger.error(f"Statcast fetch error: {e}")
            print(f"   ⚠️  Statcast error: {str(e)}")

        # 3. Apply enrichments to players
        enriched_count = 0
        for player in self.player_pool:
            enriched = False

            # Apply Vegas data
            if player.team in vegas_data:
                player.apply_vegas_data(vegas_data[player.team])
                enriched = True

            # Apply Statcast data
            if player.name in statcast_data:
                player.apply_statcast_data(statcast_data[player.name])
                enriched = True

            if enriched:
                enriched_count += 1

        print(f"\\n✅ Enriched {enriched_count}/{len(self.player_pool)} players")

        # 4. Calculate scores using unified scoring engine
        print("\\n📈 Calculating player scores...")
        for player in self.player_pool:
            try:
                # The scoring engine returns a float, not a dict
                final_score = self.scoring_engine.calculate_score(player)

                # Set the score directly
                player.optimization_score = final_score
                player.enhanced_score = final_score

                # Boost for confirmed players
                if player.is_confirmed:
                    player.optimization_score *= 1.05

            except Exception as e:
                logger.error(f"Error scoring {player.name}: {e}")
                # Use base projection as fallback
                player.optimization_score = player.base_projection
                player.enhanced_score = player.base_projection

        print("   ✅ All players scored")

        return enriched_count'''

print(method_2)

# ===========================================================================
# METHOD 3: Updated optimize_lineups to use _call_optimizer
# ===========================================================================
print("\n\n3️⃣ UPDATE optimize_lineups METHOD (find the line that calls optimize_lineup):")
print("-" * 70)
print("Find this section in optimize_lineups:")
print()
print("            # Run optimization")
print("            lineup_players, score = self.optimizer.optimize_lineup(")
print("                self.player_pool,")
print("                strategy=strategy,")
print("                min_salary_usage=self.min_salary_usage")
print("            )")
print()
print("Replace it with:")
print()

method_3 = '''            # Use the wrapper to handle optimization
            lineup_players, score = self._call_optimizer(
                players=self.player_pool,
                strategy=strategy,
                min_salary_val=self.min_salary_usage,
                existing_lineups=lineups if i > 0 else None
            )'''

print(method_3)

print("\n\n" + "=" * 70)
print("IMPLEMENTATION CHECKLIST")
print("=" * 70)
print("""
1. ✅ Add the _call_optimizer method to the class
2. ✅ Replace the entire enrich_player_pool method
3. ✅ Update the optimize_lineup call in optimize_lineups to use _call_optimizer
4. ✅ Add position mapping in load_csv (SP → P)

After these changes, your optimizer will work correctly!
""")